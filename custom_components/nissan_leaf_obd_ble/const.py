"""Constants for Nissan Leaf OBD BLE."""

from homeassistant.const import Platform

NAME = "Nissan Leaf OBD BLE"
DOMAIN = "nissan_leaf_obd_ble"

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]

# Options
CONF_CACHE_VALUES = "cache_values"
CONF_FAST_POLL = "fast_poll"
CONF_SLOW_POLL = "slow_poll"
CONF_XS_POLL = "xs_poll"
CONF_FETCH_TIMEOUT = "fetch_timeout"
CONF_SERVICE_UUID = "service_uuid"
CONF_CHARACTERISTIC_UUID_READ = "characteristic_uuid_read"
CONF_CHARACTERISTIC_UUID_WRITE = "characteristic_uuid_write"

# Defaults
DEFAULT_CACHE_VALUES = False
# When the device is in range and the car is on, poll quickly to get as much
# data as we can before it turns off.
DEFAULT_FAST_POLL = 10
# When the device is in range but the car is off, we need to poll occasionally
# to see whether the car has been turned back on. On some cars this causes a
# relay to click every time, so keep this as long as is practical.
DEFAULT_SLOW_POLL = 300
# When the device is out of range a bluetooth advertisement will trigger a
# refresh as soon as it reappears, so polling can be very slow.
DEFAULT_XS_POLL = 3600
# Cap the BLE read duration so the coordinator's refresh lock is not held
# forever; otherwise refreshes requested by BLE advertisements would no-op.
DEFAULT_FETCH_TIMEOUT = 90
DEFAULT_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
DEFAULT_CHARACTERISTIC_UUID_READ = "0000ffe1-0000-1000-8000-00805f9b34fb"
DEFAULT_CHARACTERISTIC_UUID_WRITE = "0000ffe1-0000-1000-8000-00805f9b34fb"

OVERRIDES_FILE = "custom_components/nissan_leaf_obd_ble/overrides.yaml"
DECODERS_MODULE_FILE = "custom_components/nissan_leaf_obd_ble/decoders.py"
