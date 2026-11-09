"""Test the Nissan Leaf OBD BLE config and options flows."""

from __future__ import annotations

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nissan_leaf_obd_ble.const import (
    CONF_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE,
    CONF_SERVICE_UUID,
    DEFAULT_CHARACTERISTIC_UUID_READ,
    DEFAULT_CHARACTERISTIC_UUID_WRITE,
    DEFAULT_SERVICE_UUID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ADDRESS, make_service_info

DEFAULT_UUIDS = {
    CONF_SERVICE_UUID: DEFAULT_SERVICE_UUID,
    CONF_CHARACTERISTIC_UUID_READ: DEFAULT_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE: DEFAULT_CHARACTERISTIC_UUID_WRITE,
}
DISCOVERED = (
    "custom_components.nissan_leaf_obd_ble.config_flow.async_discovered_service_info"
)
SETUP = "custom_components.nissan_leaf_obd_ble.async_setup_entry"


async def test_bluetooth_discovery(hass: HomeAssistant) -> None:
    """A discovered dongle goes straight to the confirm/UUID step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=make_service_info()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure"
    assert result["description_placeholders"] == {"name": "OBDBLE", "address": ADDRESS}

    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], DEFAULT_UUIDS
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OBDBLE"
    assert result["data"] == {CONF_ADDRESS: ADDRESS}
    assert result["options"] == DEFAULT_UUIDS
    assert result["result"].unique_id == ADDRESS


async def test_bluetooth_discovery_already_configured(hass: HomeAssistant) -> None:
    """A dongle that is already set up is not offered again."""
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=make_service_info()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow(hass: HomeAssistant) -> None:
    """The user picks a dongle, short UUIDs are expanded, bad ones rejected."""
    devices = [
        make_service_info(),
        make_service_info("Other", "11:22:33:44:55:66", service_uuids=[]),
        make_service_info("Generic", "11:22:33:44:55:77"),
    ]
    with patch(DISCOVERED, return_value=devices):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    # Matched by name or by advertised service UUID; unrelated devices are hidden.
    assert set(result["data_schema"].schema[CONF_ADDRESS].container) == {
        ADDRESS,
        "11:22:33:44:55:77",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["step_id"] == "configure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**DEFAULT_UUIDS, CONF_SERVICE_UUID: "nope"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_SERVICE_UUID: "invalid_uuid"}

    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**DEFAULT_UUIDS, CONF_SERVICE_UUID: " FFF0 "},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_SERVICE_UUID] == (
        "0000fff0-0000-1000-8000-00805f9b34fb"
    )


async def test_user_flow_no_devices(hass: HomeAssistant) -> None:
    """Abort with a translated reason when nothing is in range."""
    with patch(DISCOVERED, return_value=[]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Options are validated and merged with options not shown in the form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS},
        options={"fetch_timeout": 30},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    user_input = {
        "cache_values": True,
        "fast_poll": 5,
        "slow_poll": 600,
        "xs_poll": 3600,
        **DEFAULT_UUIDS,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**user_input, CONF_CHARACTERISTIC_UUID_READ: "xyz"}
    )
    assert result["errors"] == {CONF_CHARACTERISTIC_UUID_READ: "invalid_uuid"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"fetch_timeout": 30, **user_input}
