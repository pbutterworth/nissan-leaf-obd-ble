"""Binary sensor platform for Nissan Leaf OBD BLE."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME
from .entity import NissanLeafObdBleEntity

BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    "power_switch": BinarySensorEntityDescription(
        key="power_switch",
        # device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:power",
        name="Power switch status",
    ),
    "ac_on": BinarySensorEntityDescription(
        key="ac_on",
        # device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:air-conditioner",
        name="AC status",
    ),
    "rear_heater": BinarySensorEntityDescription(
        key="rear_heater",
        # device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:heat-wave",
        name="Rear heater status",
    ),
    "eco_mode": BinarySensorEntityDescription(
        key="eco_mode",
        # device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:sprout",
        name="ECO mode status",
    ),
    "e_pedal_mode": BinarySensorEntityDescription(
        key="e_pedal_mode",
        # device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:bike-pedal",
        name="e-Pedal mode status",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices
) -> bool:
    """Set up binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NissanLeafObdBleBinarySensor(coordinator, entry, sensor_desc)
        for sensor_desc in BINARY_SENSOR_TYPES
    ]
    async_add_devices(entities)


class NissanLeafObdBleBinarySensor(NissanLeafObdBleEntity, BinarySensorEntity):
    """nissan_leaf_obd_ble binary_sensor class."""

    def __init__(
        self,
        coordinator,
        config_entry,
        sensor: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, config_entry)
        self._sensor = sensor
        self._attr_name = f"{NAME} {BINARY_SENSOR_TYPES[sensor].name}"
        # self.entity_description = BINARY_SENSOR_TYPES[sensor]
        self._attr_device_class = BINARY_SENSOR_TYPES[sensor].device_class

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self.coordinator.data.get(self._sensor)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return BINARY_SENSOR_TYPES[self._sensor].icon
