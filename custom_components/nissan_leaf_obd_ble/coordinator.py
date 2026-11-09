"""Coordinator for Nissan Leaf OBD BLE."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from py_nissan_leaf_obd_ble import NissanLeafObdBleApiClient
from py_nissan_leaf_obd_ble.OBDCommand import OBDCommand

from homeassistant.components import bluetooth
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CACHE_VALUES,
    CONF_FAST_POLL,
    CONF_FETCH_TIMEOUT,
    CONF_SLOW_POLL,
    CONF_XS_POLL,
    DEFAULT_CACHE_VALUES,
    DEFAULT_FAST_POLL,
    DEFAULT_FETCH_TIMEOUT,
    DEFAULT_SLOW_POLL,
    DEFAULT_XS_POLL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type NissanLeafObdBleConfigEntry = ConfigEntry[NissanLeafObdBleDataUpdateCoordinator]


class NissanLeafObdBleDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the OBD dongle."""

    config_entry: NissanLeafObdBleConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: NissanLeafObdBleConfigEntry,
        extra_commands: dict[str, OBDCommand] | None = None,
        extra_sensor_descriptions: dict[str, SensorEntityDescription] | None = None,
        disabled_commands: set[str] | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=config_entry.options.get(CONF_FAST_POLL, DEFAULT_FAST_POLL)
            ),
            always_update=True,
        )
        self.address: str = config_entry.data[CONF_ADDRESS]
        self.extra_commands = extra_commands or {}
        self.extra_sensor_descriptions = extra_sensor_descriptions or {}
        self.disabled_commands = disabled_commands or set()
        self._cache_data: dict[str, Any] = {}

    def _set_poll_interval(self, option: str, default: int, reason: str) -> None:
        """Switch polling interval; options are read live so changes apply at once."""
        self.update_interval = timedelta(
            seconds=self.config_entry.options.get(option, default)
        )
        _LOGGER.debug("%s, polling interval = %s", reason, self.update_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        options = self.config_entry.options
        cache_values = options.get(CONF_CACHE_VALUES, DEFAULT_CACHE_VALUES)

        # Look the device up on every poll: the car comes and goes, and the
        # BLEDevice may be reachable through a different adapter/proxy each time.
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            self._set_poll_interval(CONF_XS_POLL, DEFAULT_XS_POLL, "Car out of range")
            return dict(self._cache_data) if cache_values else {}

        fetch_timeout = float(options.get(CONF_FETCH_TIMEOUT, DEFAULT_FETCH_TIMEOUT))
        try:
            async with asyncio.timeout(fetch_timeout):
                new_data = await NissanLeafObdBleApiClient(ble_device).async_get_data(
                    options,
                    extra_commands=self.extra_commands or None,
                    disabled_commands=self.disabled_commands or None,
                )
        except TimeoutError as err:
            raise UpdateFailed(f"BLE fetch timed out after {fetch_timeout}s") from err
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        if new_data is None:
            raise UpdateFailed("Failed to connect to OBD device")

        if new_data:
            self._set_poll_interval(CONF_FAST_POLL, DEFAULT_FAST_POLL, "Car is on")
        else:
            self._set_poll_interval(
                CONF_SLOW_POLL, DEFAULT_SLOW_POLL, "Car is probably off"
            )

        if cache_values:
            self._cache_data.update(new_data)
            return dict(self._cache_data)
        return new_data
