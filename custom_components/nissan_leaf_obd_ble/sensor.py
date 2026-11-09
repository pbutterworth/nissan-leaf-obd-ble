"""Sensor platform for Nissan Leaf OBD BLE."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import NissanLeafObdBleConfigEntry
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
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "bat_12v_current": SensorEntityDescription(
        key="bat_12v_current",
        icon="mdi:car-battery",
        name="12V battery current",
        native_unit_of_measurement="A",
        suggested_display_precision=2,
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
        suggested_display_precision=1,
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
        suggested_display_precision=0,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "odometer": SensorEntityDescription(
        key="odometer",
        name="Odometer",
        native_unit_of_measurement="km",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "tp_fr": SensorEntityDescription(
        key="tp_fr",
        name="Tyre pressure front right",
        native_unit_of_measurement="kPa",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_fl": SensorEntityDescription(
        key="tp_fl",
        name="Tyre pressure front left",
        native_unit_of_measurement="kPa",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_rr": SensorEntityDescription(
        key="tp_rr",
        name="Tyre pressure rear right",
        native_unit_of_measurement="kPa",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "tp_rl": SensorEntityDescription(
        key="tp_rl",
        name="Tyre pressure rear left",
        native_unit_of_measurement="kPa",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "range_remaining": SensorEntityDescription(
        key="range_remaining",
        name="Range remaining",
        native_unit_of_measurement="km",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "state_of_charge": SensorEntityDescription(
        key="state_of_charge",
        icon="mdi:ev-station",
        name="State of charge",
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_health": SensorEntityDescription(
        key="hv_battery_health",
        icon="mdi:battery-heart",
        name="HV battery health",
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_Ah": SensorEntityDescription(
        key="hv_battery_Ah",
        name="HV battery capacity",
        native_unit_of_measurement="Ah",
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_current_1": SensorEntityDescription(
        key="hv_battery_current_1",
        name="HV battery current 1",
        native_unit_of_measurement="A",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_current_2": SensorEntityDescription(
        key="hv_battery_current_2",
        name="HV battery current 2",
        native_unit_of_measurement="A",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_battery_voltage": SensorEntityDescription(
        key="hv_battery_voltage",
        name="HV battery voltage",
        native_unit_of_measurement="V",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NissanLeafObdBleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = entry.runtime_data
    # User-defined sensors from overrides.yaml replace built-in ones with the same key.
    descriptions = {**SENSOR_TYPES, **coordinator.extra_sensor_descriptions}
    async_add_entities(
        NissanLeafObdBleSensor(coordinator, description)
        for description in descriptions.values()
    )


class NissanLeafObdBleSensor(NissanLeafObdBleEntity, SensorEntity):
    """nissan_leaf_obd_ble sensor class."""

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
