"""Load user-defined OBD command overrides for the Nissan Leaf integration."""

import importlib.util
import logging
import struct
from pathlib import Path
from typing import Any, Callable

import yaml
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant

from py_nissan_leaf_obd_ble.OBDCommand import OBDCommand
from py_nissan_leaf_obd_ble.commands import leaf_commands

from .const import DECODERS_MODULE_FILE, OVERRIDES_FILE

_LOGGER = logging.getLogger(__name__)

_DEVICE_CLASSES: dict[str, SensorDeviceClass] = {
    "battery": SensorDeviceClass.BATTERY,
    "current": SensorDeviceClass.CURRENT,
    "distance": SensorDeviceClass.DISTANCE,
    "energy": SensorDeviceClass.ENERGY,
    "enum": SensorDeviceClass.ENUM,
    "power": SensorDeviceClass.POWER,
    "pressure": SensorDeviceClass.PRESSURE,
    "speed": SensorDeviceClass.SPEED,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "voltage": SensorDeviceClass.VOLTAGE,
}

_STATE_CLASSES: dict[str, SensorStateClass] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


def load_overrides(
    hass: HomeAssistant, address: str
) -> tuple[dict[str, OBDCommand], dict[str, SensorEntityDescription], set[str]]:
    """Return (extra_commands, extra_sensor_descriptions, disabled_commands) for a BLE address.

    Reads overrides.yaml and optionally decoders.py from the integration config directory.
    Safe to call from an executor thread (synchronous I/O only).
    """
    overrides_path = Path(hass.config.config_dir) / OVERRIDES_FILE
    decoders_path = Path(hass.config.config_dir) / DECODERS_MODULE_FILE

    python_module = None
    if decoders_path.exists():
        python_module = _load_python_module(decoders_path)

    if not overrides_path.exists():
        return {}, {}, set()

    try:
        with open(overrides_path) as f:
            config = yaml.safe_load(f)
    except Exception as err:
        _LOGGER.error("Failed to load %s: %s", overrides_path, err)
        return {}, {}, set()

    if not config:
        return {}, {}, set()

    # Merge _all_ entries with address-specific entries; address-specific wins on conflict
    command_entries: dict[str, Any] = {}
    if "_all_" in config:
        command_entries.update(((config["_all_"] or {}).get("commands", {})))
    address_upper = address.upper()
    if address_upper in config:
        command_entries.update(((config[address_upper] or {}).get("commands", {})))

    extra_commands: dict[str, OBDCommand] = {}
    extra_sensor_descriptions: dict[str, SensorEntityDescription] = {}
    disabled_commands: set[str] = set()

    for key, entry in command_entries.items():
        entry = entry or {}

        if not entry.get("enabled", True):
            disabled_commands.add(key)
            continue

        try:
            cmd = _build_command(key, entry, python_module)
        except Exception as err:
            _LOGGER.error("Invalid override for command '%s': %s", key, err)
            continue

        extra_commands[key] = cmd

        if "sensor" in entry and key not in leaf_commands:
            try:
                extra_sensor_descriptions.update(_build_sensor_descriptions(key, entry))
            except Exception as err:
                _LOGGER.error("Invalid sensor definition for command '%s': %s", key, err)

    return extra_commands, extra_sensor_descriptions, disabled_commands


def _load_python_module(path: Path):
    """Load a Python module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location("nissan_leaf_obd_ble_decoders", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _LOGGER.info("Loaded custom decoders from %s", path)
        return module
    except Exception as err:
        _LOGGER.error("Failed to load custom decoders from %s: %s", path, err)
        return None


def _build_command(key: str, entry: dict, python_module) -> OBDCommand:
    """Build an OBDCommand, inheriting unspecified fields from the base command if it exists."""
    base = leaf_commands.get(key)

    if "command" in entry:
        command = entry["command"].encode()
    elif base is not None:
        command = base.command
    else:
        raise ValueError(f"'command' is required for new command '{key}'")

    if "header" in entry:
        header = entry["header"].encode()
    elif base is not None:
        header = base.header
    else:
        raise ValueError(f"'header' is required for new command '{key}'")

    if "bytes" in entry:
        byte_count = int(entry["bytes"])
    elif base is not None:
        byte_count = base.bytes
    else:
        raise ValueError(f"'bytes' is required for new command '{key}'")

    if "decoder" in entry:
        decoder = _build_decoder(key, entry["decoder"], python_module)
    elif base is not None:
        decoder = base.decode
    else:
        raise ValueError(f"'decoder' is required for new command '{key}'")

    desc = entry.get("description", base.desc if base else key)

    return OBDCommand(key, desc, command, byte_count, decoder, header)


def _build_decoder(key: str, spec: dict, python_module) -> Callable:
    """Build a decoder function from a YAML decoder spec dict."""
    decoder_type = spec.get("type")
    if not decoder_type:
        raise ValueError(f"Decoder spec for '{key}' is missing 'type'")

    if decoder_type == "linear_scale":
        byte_offset = int(spec["byte_offset"])
        scale = float(spec.get("scale", 1.0))
        offset = float(spec.get("offset", 0.0))

        def _linear(messages, _key=key, _off=byte_offset, _scale=scale, _add=offset):
            return {_key: messages[0].data[_off] * _scale + _add}

        return _linear

    if decoder_type == "multi_byte_int":
        byte_start = int(spec["byte_start"])
        byte_end = int(spec["byte_end"])
        signed = bool(spec.get("signed", False))
        byte_order = spec.get("byte_order", "big")
        scale = float(spec.get("scale", 1.0))
        offset = float(spec.get("offset", 0.0))

        def _multi_byte(
            messages,
            _key=key,
            _start=byte_start,
            _end=byte_end,
            _signed=signed,
            _order=byte_order,
            _scale=scale,
            _add=offset,
        ):
            v = int.from_bytes(messages[0].data[_start:_end], _order, signed=_signed)
            return {_key: v * _scale + _add}

        return _multi_byte

    if decoder_type == "struct_unpack":
        fmt = spec["format"]
        byte_start = int(spec["byte_start"])
        byte_end = int(spec["byte_end"])
        scale = float(spec.get("scale", 1.0))
        offset = float(spec.get("offset", 0.0))

        def _struct(
            messages,
            _key=key,
            _fmt=fmt,
            _start=byte_start,
            _end=byte_end,
            _scale=scale,
            _add=offset,
        ):
            v = struct.unpack(_fmt, messages[0].data[_start:_end])[0]
            return {_key: v * _scale + _add}

        return _struct

    if decoder_type == "lookup":
        byte_offset = int(spec["byte_offset"])
        values = {int(k): v for k, v in spec["values"].items()}
        default = spec.get("default")

        def _lookup(messages, _key=key, _off=byte_offset, _values=values, _default=default):
            return {_key: _values.get(messages[0].data[_off], _default)}

        return _lookup

    if decoder_type == "bit_flag":
        byte_offset = int(spec["byte_offset"])
        bit_mask = int(str(spec["bit_mask"]), 0)

        def _bit_flag(messages, _key=key, _off=byte_offset, _mask=bit_mask):
            return {_key: (messages[0].data[_off] & _mask) == _mask}

        return _bit_flag

    if decoder_type == "equality":
        byte_offset = int(spec["byte_offset"])
        value = int(str(spec["value"]), 0)

        def _equality(messages, _key=key, _off=byte_offset, _val=value):
            return {_key: messages[0].data[_off] == _val}

        return _equality

    if decoder_type == "multi_field":
        fields = spec["fields"]
        sub_decoders = [
            _build_decoder(field["key"], field, python_module) for field in fields
        ]

        def _multi_field(messages, _subs=sub_decoders):
            result = {}
            for sub in _subs:
                result.update(sub(messages))
            return result

        return _multi_field

    if decoder_type == "python":
        func_name = spec.get("function")
        if not func_name:
            raise ValueError(
                f"Decoder type 'python' for '{key}' requires a 'function' name"
            )
        if python_module is None:
            raise ValueError(
                f"Decoder type 'python' for '{key}' requires "
                f"'{DECODERS_MODULE_FILE}' to be present in the integration directory"
            )
        func = getattr(python_module, func_name, None)
        if func is None:
            raise ValueError(
                f"Function '{func_name}' not found in '{DECODERS_MODULE_FILE}'"
            )
        return func

    raise ValueError(f"Unknown decoder type '{decoder_type}' for command '{key}'")


def _build_sensor_descriptions(
    key: str, entry: dict
) -> dict[str, SensorEntityDescription]:
    """Build SensorEntityDescription(s) from the sensor: block of an override entry."""
    sensor_block = entry["sensor"]
    decoder_type = (entry.get("decoder") or {}).get("type")

    if decoder_type == "multi_field":
        if not isinstance(sensor_block, list):
            raise ValueError(f"'sensor' must be a list for multi_field command '{key}'")
        return {
            field["key"]: _sensor_desc_from_block(field["key"], field)
            for field in sensor_block
        }

    return {key: _sensor_desc_from_block(key, sensor_block)}


def _sensor_desc_from_block(key: str, block: dict) -> SensorEntityDescription:
    """Build a SensorEntityDescription from a sensor config block."""
    device_class_str = block.get("device_class")
    device_class = _DEVICE_CLASSES.get(device_class_str) if device_class_str else None

    state_class_str = block.get("state_class")
    state_class = _STATE_CLASSES.get(state_class_str) if state_class_str else None

    return SensorEntityDescription(
        key=key,
        name=block.get("name", key),
        native_unit_of_measurement=block.get("unit"),
        device_class=device_class,
        state_class=state_class,
        suggested_display_precision=block.get("precision"),
        icon=block.get("icon"),
    )
