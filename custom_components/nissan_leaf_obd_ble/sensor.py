"""Sensor platform for Nissan Leaf OBD BLE."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME
from .entity import NissanLeafObdBleEntity

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "gear_position": SensorEntityDescription(
        key="gear_position",
        icon="mdi:car-shift-pattern",
        name="Gear position",
        device_class=SensorDeviceClass.ENUM,
    ),
    "bat_12v_voltage": SensorEntityDescription(
        key="bat_12v_voltage",
        icon="mdi:car-battery",
        name="12V battery voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "bat_12v_current": SensorEntityDescription(
        key="bat_12v_current",
        icon="mdi:car-battery",
        name="12V battery current",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "quick_charges": SensorEntityDescription(
        key="quick_charges",
        icon="mdi:ev-plug-chademo",
        name="Number of quick charges",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "l1_l2_charges": SensorEntityDescription(
        key="l1_l2_charges",
        icon="mdi:ev-plug-type2",
        name="Number of L1/L2 charges",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "ambient_temp": SensorEntityDescription(
        key="ambient_temp",
        icon="mdi:thermometer",
        name="Ambient temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "estimated_ac_power": SensorEntityDescription(
        key="estimated_ac_power",
        icon="mdi:air-conditioner",
        name="Estimated AC system power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "estimated_ptc_power": SensorEntityDescription(
        key="estimated_ptc_power",
        icon="mdi:heating-coil",
        name="Estimated PTC system power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "aux_power": SensorEntityDescription(
        key="aux_power",
        icon="mdi:generator-portable",
        name="Auxiliary equipment power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "ac_power": SensorEntityDescription(
        key="ac_power",
        icon="mdi:air-conditioner",
        name="AC system power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "plug_state": SensorEntityDescription(
        key="plug_state",
        icon="mdi:ev-plug-type1",
        name="Plug state of J1772 socket",
        device_class=SensorDeviceClass.ENUM,
    ),
    "charge_mode": SensorEntityDescription(
        key="charge_mode",
        icon="mdi:ev-station",
        name="Charging mode",
        device_class=SensorDeviceClass.ENUM,
    ),
    "rpm": SensorEntityDescription(
        key="rpm",
        icon="mdi:gauge",
        name="Motor RPM",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "obc_out_power": SensorEntityDescription(
        key="obc_out_power",
        icon="mdi:generator-mobile",
        name="On-board charger output power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "motor_power": SensorEntityDescription(
        key="motor_power",
        icon="mdi:engine",
        name="Traction motor power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "speed": SensorEntityDescription(
        key="speed",
        icon="mdi:speedometer",
        name="Vehicle speed",
        native_unit_of_measurement="km/h",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "odometer": SensorEntityDescription(
        key="odometer",
        # icon="mdi:speedometer",
        name="Odometer",
        native_unit_of_measurement="km",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "tp_fr": SensorEntityDescription(
        key="tp_fr",
        # icon="mdi:speedometer",
        name="Tyre pressure front right",
        native_unit_of_measurement="kPa",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_fl": SensorEntityDescription(
        key="tp_fl",
        # icon="mdi:speedometer",
        name="Tyre pressure front left",
        native_unit_of_measurement="kPa",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_rr": SensorEntityDescription(
        key="tp_rr",
        # icon="mdi:speedometer",
        name="Tyre pressure rear right",
        native_unit_of_measurement="kPa",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_rl": SensorEntityDescription(
        key="tp_rl",
        # icon="mdi:speedometer",
        name="Tyre pressure rear left",
        native_unit_of_measurement="kPa",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "range_remaining": SensorEntityDescription(
        key="range_remaining",
        # icon="mdi:speedometer",
        name="Range remaining",
        native_unit_of_measurement="km",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "state_of_charge": SensorEntityDescription(
        key="state_of_charge",
        icon="mdi:ev-station",
        name="State of charge",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_health": SensorEntityDescription(
        key="hv_battery_health",
        icon="mdi:battery-heart",
        name="HV battery health",
        native_unit_of_measurement="%",
        # device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_Ah": SensorEntityDescription(
        key="hv_battery_Ah",
        # icon="mdi:ev-station",
        name="HV battery capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_current_1": SensorEntityDescription(
        key="hv_battery_current_1",
        # icon="mdi:ev-station",
        name="HV battery current 1",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_current_2": SensorEntityDescription(
        key="hv_battery_current_2",
        # icon="mdi:ev-station",
        name="HV battery current 2",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_voltage": SensorEntityDescription(
        key="hv_battery_voltage",
        # icon="mdi:ev-station",
        name="HV battery voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NissanLeafObdBleSensor(coordinator, entry, sensor_desc)
        for sensor_desc in SENSOR_TYPES
    ]
    async_add_entities(entities)

    # async_add_devices([NissanLeafObdBleSensor(coordinator, entry)])


class NissanLeafObdBleSensor(NissanLeafObdBleEntity, SensorEntity):
    """Config entry for nissan_leaf_obd_ble sensors."""

    def __init__(
        self,
        coordinator,
        config_entry,
        sensor: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._sensor = sensor
        self._attr_name = f"{NAME} {SENSOR_TYPES[sensor].name}"
        # self.entity_description = CHLORINATOR_SENSOR_TYPES[sensor]
        self._attr_device_class = SENSOR_TYPES[sensor].device_class
        self._attr_native_unit_of_measurement = SENSOR_TYPES[
            sensor
        ].native_unit_of_measurement

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return SENSOR_TYPES[self._sensor].icon
