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
        self._result: dict = None

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        self._result = {}

        if self._ble_device is None:
            return self._result

        api = await OBD.create(self._ble_device, protocol="6")

        if api is None:
            return None

        data = {}
        for command in leaf_commands.values():
            response = await api.query(command, force=True)
            if len(response.messages) == 0:
                break
            if response.value is not None:
                data.update(response.value)  # send the command, and parse the response
        _LOGGER.debug("Returning data: %s", data)
        await api.close()
        return data
