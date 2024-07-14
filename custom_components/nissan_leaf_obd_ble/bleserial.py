import asyncio
import logging

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class bleserial:
    """Encapsulates the ble connection and make it appear something like a UART port."""

    __buffer = bytearray()

    def __init__(self, device: BLEDevice, service_uuid, characteristic_uuid) -> None:
        self.device = device
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid
        self.client = None
        self._rx_buffer = bytearray()
        self._timeout = None

    async def _wait_for_data(self, size):
        while len(self._rx_buffer) < size:
            await asyncio.sleep(0.01)

    async def _wait_for_line(self):
        while b"\n" not in self._rx_buffer:
            await asyncio.sleep(0.01)

    def reset_input_buffer(self):
        logger.debug("Resetting input buffer")
        self._rx_buffer.clear()

    def reset_output_buffer(self):
        logger.debug("Resetting output buffer")
        # Since there's no explicit output buffer, this is a no-op.

    def flush(self):
        self.reset_input_buffer()
        self.reset_output_buffer()

    @property
    def in_waiting(self):
        return len(self._rx_buffer)

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def write_timeout(self):
        return self._write_timeout

    @write_timeout.setter
    def write_timeout(self, value):
        self._write_timeout = value

    def _notification_handler(self, sender, data):
        logger.debug("Notification received: %s", data)
        self._rx_buffer.extend(data)

    async def open(self):
        self.client = BleakClient(self.device)
        try:
            logger.debug("Connecting to device: %s", self.device)
            await self.client.connect()
            logger.debug("Connected to device: %s", self.device)
            logger.debug(
                "Starting notifications on characteristic UUID: %s",
                self.characteristic_uuid,
            )
            await self.client.start_notify(
                self.characteristic_uuid, self._notification_handler
            )
            logger.debug("Notifications started")
        except BleakError as e:
            logger.error("Failed to connect or start notifications: %s", e)
            raise

    async def close(self):
        if self.client:
            try:
                logger.debug(
                    "Stopping notifications on characteristic UUID: %s",
                    self.characteristic_uuid,
                )
                await self.client.stop_notify(self.characteristic_uuid)
                logger.debug("Notifications stopped")
                logger.debug("Disconnecting from device")
                await self.client.disconnect()
                logger.debug("Disconnected from device")
            except BleakError as e:
                logger.error("Failed to stop notifications or disconnect: %s", e)
                raise

    async def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        try:
            logger.info(
                "Writing data to characteristic UUID: %s Data: %s",
                self.characteristic_uuid,
                data,
            )
            await self.client.write_gatt_char(self.characteristic_uuid, data)
            logger.debug("Data written")
        except BleakError as e:
            logger.error("Failed to write data: %s", e)
            raise

    async def read(self, size=1):
        try:
            logger.debug("Reading %s bytes of data", size)
            while len(self._rx_buffer) < size:
                await asyncio.sleep(0.01)
            data = self._rx_buffer[:size]
            self._rx_buffer = self._rx_buffer[size:]
            logger.debug("Read data: %s", data)
            return bytes(data)
        except Exception as e:
            logger.error("Failed to read data: %s", e)
            raise

    async def readline(self):
        try:
            logger.debug("Reading line")
            await asyncio.wait_for(self._wait_for_line(), timeout=self._timeout)
            index = self._rx_buffer.index(b"\n") + 1
            data = self._rx_buffer[:index]
            self._rx_buffer = self._rx_buffer[index:]
            logger.debug("Read line: %s", data)
            return bytes(data)
        except asyncio.TimeoutError:
            logger.error("Readline operation timed out")
            raise BleakError("Readline operation timed out")
        except Exception as e:
            logger.error("Failed to read line: %s", e)
            raise


# # Example usage:
# async def main():
#     service_uuid = "0000ffe0-0000-1000-8000-00805f9b34fb"  # Replace with your service UUID
#     characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Replace with your characteristic UUID

#     async_serial = bleserial(service_uuid, characteristic_uuid)
#     try:
#         await async_serial.open()

#         await async_serial.write("ATZ\r")
#         response = await async_serial.read(2)
#         print("Received:", response)

#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         await async_serial.close()

# asyncio.run(main())
