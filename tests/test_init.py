"""Test setup, polling and unloading of Nissan Leaf OBD BLE."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nissan_leaf_obd_ble.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ADDRESS, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import ADDRESS, make_service_info

BLE_DEVICE = "homeassistant.components.bluetooth.async_ble_device_from_address"
GET_DATA = (
    "custom_components.nissan_leaf_obd_ble.coordinator"
    ".NissanLeafObdBleApiClient.async_get_data"
)


def _entry(hass: HomeAssistant, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        title="OBDBLE",
        data={CONF_ADDRESS: ADDRESS},
        options=options,
    )
    entry.add_to_hass(hass)
    return entry


async def test_setup_car_away(hass: HomeAssistant) -> None:
    """Setup succeeds with the car out of range and polls very slowly."""
    entry = _entry(hass)
    with patch(BLE_DEVICE, return_value=None):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.update_interval == timedelta(seconds=3600)
    state = hass.states.get("sensor.nissan_leaf_obd_ble_state_of_charge")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_with_data_and_cache(hass: HomeAssistant) -> None:
    """Data reaches the entities, and cached values survive the car leaving."""
    entry = _entry(hass, cache_values=True, fast_poll=7)
    data = {"state_of_charge": 81.5, "power_switch": True, "gear_position": "Park"}
    with (
        patch(BLE_DEVICE, return_value=make_service_info().device),
        patch(GET_DATA, AsyncMock(return_value=data)) as get_data,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert get_data.await_args.args[0] == entry.options
    coordinator = entry.runtime_data
    assert coordinator.update_interval == timedelta(seconds=7)
    assert hass.states.get("sensor.nissan_leaf_obd_ble_state_of_charge").state == "81.5"
    assert (
        hass.states.get("binary_sensor.nissan_leaf_obd_ble_power_switch_status").state
        == "on"
    )
    assert hass.states.get("button.nissan_leaf_obd_ble_refresh") is not None

    registry = er.async_get(hass)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}-state_of_charge")

    with patch(BLE_DEVICE, return_value=None):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert hass.states.get("sensor.nissan_leaf_obd_ble_state_of_charge").state == "81.5"


async def test_car_off_uses_slow_poll_and_failure_marks_unavailable(
    hass: HomeAssistant,
) -> None:
    """An empty response means the car is off; a failed connect is an error."""
    entry = _entry(hass)
    with (
        patch(BLE_DEVICE, return_value=make_service_info().device),
        patch(GET_DATA, AsyncMock(return_value={})),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = entry.runtime_data
    assert coordinator.update_interval == timedelta(seconds=300)

    with (
        patch(BLE_DEVICE, return_value=make_service_info().device),
        patch(GET_DATA, AsyncMock(return_value=None)),
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert coordinator.last_update_success is False
    assert (
        hass.states.get("sensor.nissan_leaf_obd_ble_state_of_charge").state
        == "unavailable"
    )
    assert hass.states.get("button.nissan_leaf_obd_ble_refresh").state != "unavailable"


async def test_unique_id_migration(hass: HomeAssistant) -> None:
    """Old name-based unique IDs are migrated, keeping the entity IDs."""
    entry = _entry(hass)
    registry = er.async_get(hass)
    old = {
        "sensor": ("Nissan Leaf OBD BLE State of charge", "state_of_charge"),
        "binary_sensor": ("Nissan Leaf OBD BLE AC status", "ac_on"),
        "button": ("Nissan Leaf OBD BLE Refresh", "refresh"),
    }
    for domain, (name, _key) in old.items():
        registry.async_get_or_create(
            domain,
            DOMAIN,
            f"{ADDRESS}-{name}",
            config_entry=entry,
            suggested_object_id=f"legacy_{domain}",
        )

    with patch(BLE_DEVICE, return_value=None):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    for domain, (_name, key) in old.items():
        assert (
            registry.async_get_entity_id(domain, DOMAIN, f"{ADDRESS}-{key}")
            == f"{domain}.legacy_{domain}"
        )
