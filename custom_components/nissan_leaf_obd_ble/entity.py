"""NissanLeafObdBleEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import NissanLeafObdBleDataUpdateCoordinator


class NissanLeafObdBleEntity(CoordinatorEntity[NissanLeafObdBleDataUpdateCoordinator]):
    """Base entity for nissan_leaf_obd_ble."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NissanLeafObdBleDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=NAME,
            manufacturer="Nissan",
            model="Leaf",
        )
