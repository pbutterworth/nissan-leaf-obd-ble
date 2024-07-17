"""API for nissan leaf obd ble."""

# import asyncio
import logging

from bleak.backends.device import BLEDevice

from .commands import leaf_commands
from .obd import OBD

_LOGGER: logging.Logger = logging.getLogger(__package__)


class NissanLeafObdBleApiClient:
    """API for connecting to the Nissan Leaf OBD BLE dongle."""

    def __init__(
        self,
        ble_device: BLEDevice,
    ) -> None:
        """Initialise."""
        self._ble_device = ble_device

    async def async_get_data(self) -> dict:
        """Get data from the API."""

        if self._ble_device is None:
            return {}

        api = await OBD.create(self._ble_device, protocol="6")

        if api is None:
            return None

        data = {}
        for command in leaf_commands.values():
            response = await api.query(command, force=True)
            # the first command is the Mystery command. If this doesn't have a response, then none of the other will
            if command.name == "unknown" and len(response.messages) == 0:
                break
            if response.value is not None:
                data.update(response.value)  # send the command, and parse the response
        _LOGGER.debug("Returning data: %s", data)
        await api.close()
        return data
