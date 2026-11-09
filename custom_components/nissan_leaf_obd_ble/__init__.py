"""Custom integration to integrate Nissan Leaf OBD BLE with Home Assistant.

For more details about this integration, please refer to
https://github.com/pbutterworth/nissan-leaf-obd-ble
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .binary_sensor import BINARY_SENSOR_TYPES
from .button import REFRESH_BUTTON
from .const import NAME, PLATFORMS
from .coordinator import (
    NissanLeafObdBleConfigEntry,
    NissanLeafObdBleDataUpdateCoordinator,
)
from .overrides import load_overrides
from .sensor import SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: NissanLeafObdBleConfigEntry
) -> bool:
    """Set up this integration using UI."""
    address: str = entry.data[CONF_ADDRESS]

    (
        extra_commands,
        extra_sensor_descriptions,
        disabled_commands,
    ) = await hass.async_add_executor_job(load_overrides, hass, address)

    coordinator = NissanLeafObdBleDataUpdateCoordinator(
        hass,
        entry,
        extra_commands=extra_commands,
        extra_sensor_descriptions=extra_sensor_descriptions,
        disabled_commands=disabled_commands,
    )

    await _async_migrate_unique_ids(hass, entry, coordinator)

    # The car is often away or asleep when Home Assistant starts. That is not a
    # setup failure: the coordinator returns no data and the advertisement
    # callback below triggers a refresh as soon as the dongle is seen again.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _async_device_seen(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Refresh immediately when the device comes back in range."""
        _LOGGER.debug("New service_info: %s - %s", service_info, change)
        entry.async_create_background_task(
            hass, coordinator.async_request_refresh(), "nissan_leaf_obd_ble_seen"
        )

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_device_seen,
            bluetooth.BluetoothCallbackMatcher(address=address, connectable=True),
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: NissanLeafObdBleConfigEntry
) -> None:
    """Apply new options straight away (the coordinator reads them live)."""
    await entry.runtime_data.async_request_refresh()


async def async_unload_entry(
    hass: HomeAssistant, entry: NissanLeafObdBleConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_migrate_unique_ids(
    hass: HomeAssistant,
    entry: NissanLeafObdBleConfigEntry,
    coordinator: NissanLeafObdBleDataUpdateCoordinator,
) -> None:
    """Migrate unique IDs from the old '<address>-<entity name>' form to '<address>-<key>'.

    Entity names are user-facing and may change; keys are stable.
    """
    address = coordinator.address
    old_prefix = f"{address}-{NAME} "
    key_by_name: dict[tuple[str, str], str] = {
        (Platform.BUTTON, str(REFRESH_BUTTON.name)): REFRESH_BUTTON.key
    }
    for platform, descriptions in (
        (Platform.SENSOR, SENSOR_TYPES),
        (Platform.SENSOR, coordinator.extra_sensor_descriptions),
        (Platform.BINARY_SENSOR, BINARY_SENSOR_TYPES),
    ):
        for description in descriptions.values():
            key_by_name[(platform, str(description.name))] = description.key

    @callback
    def _migrate(entity_entry: er.RegistryEntry) -> dict[str, Any] | None:
        if not entity_entry.unique_id.startswith(old_prefix):
            return None
        old_name = entity_entry.unique_id.removeprefix(old_prefix)
        if (key := key_by_name.get((entity_entry.domain, old_name))) is None:
            return None
        return {"new_unique_id": f"{address}-{key}"}

    try:
        await er.async_migrate_entries(hass, entry.entry_id, _migrate)
    except ValueError as err:
        _LOGGER.warning("Could not migrate entity unique IDs: %s", err)
