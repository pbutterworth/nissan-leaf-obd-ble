"""Fixtures for the Nissan Leaf OBD BLE tests."""

from __future__ import annotations

from home_assistant_bluetooth import BluetoothServiceInfoBleak
import pytest

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

ADDRESS = "AA:BB:CC:DD:EE:FF"
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"


def make_service_info(
    name: str = "OBDBLE",
    address: str = ADDRESS,
    service_uuids: list[str] | None = None,
) -> BluetoothServiceInfoBleak:
    """Build a bluetooth advertisement for a dongle."""
    uuids = [SERVICE_UUID] if service_uuids is None else service_uuids
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=uuids,
        source="local",
        device=BLEDevice(address, name, {}),
        advertisement=AdvertisementData(
            local_name=name,
            manufacturer_data={},
            service_data={},
            service_uuids=uuids,
            tx_power=None,
            rssi=-60,
            platform_data=(),
        ),
        connectable=True,
        time=0,
        tx_power=None,
    )


@pytest.fixture(autouse=True)
def auto_enable(enable_custom_integrations: None, mock_bluetooth: None) -> None:
    """Load custom integrations and mock the bluetooth stack in every test."""
