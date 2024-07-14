"""Custom integration to integrate Nissan Leaf OBD BLE with Home Assistant.

For more details about this integration, please refer to
https://github.com/pbutterworth/nissan-leaf-obd-ble
"""

import asyncio
from datetime import timedelta
import logging

from bleak_retry_connector import get_device

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NissanLeafObdBleApiClient
from .const import DOMAIN, PLATFORMS, STARTUP_MESSAGE

SCAN_INTERVAL = timedelta(minutes=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), True
    ) or await get_device(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find chlorinator device with address {address}"
        )

    client = NissanLeafObdBleApiClient(ble_device)

    coordinator = NissanLeafObdBleDataUpdateCoordinator(hass, client=client)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            # hass.async_create_task(
            await hass.config_entries.async_forward_entry_setup(entry, platform)
            # )

    entry.add_update_listener(async_reload_entry)
    return True


class NissanLeafObdBleDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: NissanLeafObdBleApiClient,
    ) -> None:
        """Initialize."""
        self._data = {}
        self.api = client
        self.platforms = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            self._data.update(await self.api.async_get_data())
        except Exception as exception:
            raise UpdateFailed from exception
        else:
            return self._data


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            [
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
