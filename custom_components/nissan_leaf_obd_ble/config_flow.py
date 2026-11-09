"""Config flow for Nissan Leaf OBD BLE."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from bleak.uuids import normalize_uuid_str
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import (
    CONF_CACHE_VALUES,
    CONF_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE,
    CONF_FAST_POLL,
    CONF_SERVICE_UUID,
    CONF_SLOW_POLL,
    CONF_XS_POLL,
    DEFAULT_CACHE_VALUES,
    DEFAULT_CHARACTERISTIC_UUID_READ,
    DEFAULT_CHARACTERISTIC_UUID_WRITE,
    DEFAULT_FAST_POLL,
    DEFAULT_SERVICE_UUID,
    DEFAULT_SLOW_POLL,
    DEFAULT_XS_POLL,
    DOMAIN,
)

LOCAL_NAMES = ("OBDBLE",)

UUID_DEFAULTS: dict[str, str] = {
    CONF_SERVICE_UUID: DEFAULT_SERVICE_UUID,
    CONF_CHARACTERISTIC_UUID_READ: DEFAULT_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE: DEFAULT_CHARACTERISTIC_UUID_WRITE,
}

UUID_SCHEMA = {vol.Required(key): str for key in UUID_DEFAULTS}

_POLL_INTERVAL = vol.All(vol.Coerce(int), vol.Range(min=1))


def _validate_uuids(user_input: dict[str, Any]) -> dict[str, str]:
    """Normalise the UUID fields in place and return any form errors."""
    errors: dict[str, str] = {}
    for key in UUID_DEFAULTS:
        try:
            user_input[key] = str(UUID(normalize_uuid_str(user_input[key].strip())))
        except (ValueError, AttributeError):
            errors[key] = "invalid_uuid"
    return errors


def _is_supported_device(service_info: BluetoothServiceInfoBleak) -> bool:
    """Return true if the advertisement looks like a supported OBD dongle."""
    return (
        service_info.name.startswith(LOCAL_NAMES)
        or DEFAULT_SERVICE_UUID in service_info.service_uuids
    )


class NissanLeafObdBleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow handler."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self._selected_device: BluetoothServiceInfoBleak | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return NissanLeafObdBleOptionsFlowHandler()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a device found by bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._selected_device = discovery_info
        self.context["title_placeholders"] = {
            "name": f"{discovery_info.name} ({discovery_info.address})"
        }
        return await self.async_step_configure()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick one of the discovered devices."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._selected_device = self._discovered_devices[address]
            return await self.async_step_configure()

        current_addresses = self._async_current_ids(include_ignore=False)
        candidates = [
            service_info
            for service_info in async_discovered_service_info(self.hass)
            if service_info.address not in current_addresses
        ]
        # Prefer devices that look like a supported dongle. If none do, offer
        # every connectable device so dongles with another name/UUID can be added.
        supported = [info for info in candidates if _is_supported_device(info)]
        self._discovered_devices = {
            info.address: info for info in supported or candidates
        }

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{service_info.name} ({address})"
                            for address, service_info in self._discovered_devices.items()
                        }
                    ),
                }
            ),
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the device and configure its GATT UUIDs."""
        assert self._selected_device is not None
        device = self._selected_device
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_uuids(user_input)
            if not errors:
                return self.async_create_entry(
                    title=device.name or device.address,
                    data={CONF_ADDRESS: device.address},
                    options=user_input,
                )

        return self.async_show_form(
            step_id="configure",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(UUID_SCHEMA), user_input or UUID_DEFAULTS
            ),
            description_placeholders={
                "name": device.name or device.address,
                "address": device.address,
            },
            errors=errors,
        )


class NissanLeafObdBleOptionsFlowHandler(OptionsFlow):
    """Options flow handler for nissan_leaf_obd_ble."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_uuids(user_input)
            if not errors:
                # Keep any options that are not exposed in the form.
                return self.async_create_entry(
                    data={**self.config_entry.options, **user_input}
                )

        defaults = {
            CONF_CACHE_VALUES: DEFAULT_CACHE_VALUES,
            CONF_FAST_POLL: DEFAULT_FAST_POLL,
            CONF_SLOW_POLL: DEFAULT_SLOW_POLL,
            CONF_XS_POLL: DEFAULT_XS_POLL,
            **UUID_DEFAULTS,
        }
        # Older entries may hold empty/None UUIDs; fall back to the defaults.
        stored = {k: v for k, v in self.config_entry.options.items() if v is not None}

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_CACHE_VALUES): bool,
                        vol.Required(CONF_FAST_POLL): _POLL_INTERVAL,
                        vol.Required(CONF_SLOW_POLL): _POLL_INTERVAL,
                        vol.Required(CONF_XS_POLL): _POLL_INTERVAL,
                        **UUID_SCHEMA,
                    }
                ),
                user_input or {**defaults, **stored},
            ),
            errors=errors,
        )
