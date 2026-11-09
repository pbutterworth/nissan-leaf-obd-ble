"""Binary sensor platform for Nissan Leaf OBD BLE."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import NissanLeafObdBleConfigEntry
from .entity import NissanLeafObdBleEntity

BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    "power_switch": BinarySensorEntityDescription(
        key="power_switch",
        icon="mdi:power",
        name="Power switch status",
    ),
    "ac_on": BinarySensorEntityDescription(
        key="ac_on",
        icon="mdi:air-conditioner",
        name="AC status",
    ),
    "rear_heater": BinarySensorEntityDescription(
        key="rear_heater",
        icon="mdi:heat-wave",
        name="Rear heater status",
    ),
    "eco_mode": BinarySensorEntityDescription(
        key="eco_mode",
        icon="mdi:sprout",
        name="ECO mode status",
    ),
    "e_pedal_mode": BinarySensorEntityDescription(
        key="e_pedal_mode",
        icon="mdi:bike-pedal",
        name="e-Pedal mode status",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NissanLeafObdBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary_sensor platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        NissanLeafObdBleBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES.values()
    )


class NissanLeafObdBleBinarySensor(NissanLeafObdBleEntity, BinarySensorEntity):
    """nissan_leaf_obd_ble binary_sensor class."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary_sensor is on."""
        return self.coordinator.data.get(self.entity_description.key)
