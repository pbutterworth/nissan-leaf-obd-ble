"""Part of python-OBD (a derivative of pyOBD)."""
########################################################################
#                                                                      #
# python-OBD: A python OBD-II serial module derived from pyobd         #
#                                                                      #
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)                 #
# Copyright 2009 Secons Ltd. (www.obdtester.com)                       #
# Copyright 2009 Peter J. Creath                                       #
# Copyright 2016 Brendan Whitfield (brendan-w.com)                     #
#                                                                      #
########################################################################
#                                                                      #
# decoders.py                                                          #
#                                                                      #
# This file is part of python-OBD (a derivative of pyOBD)              #
#                                                                      #
# python-OBD is free software: you can redistribute it and/or modify   #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 2 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# python-OBD is distributed in the hope that it will be useful,        #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with python-OBD.  If not, see <http://www.gnu.org/licenses/>.  #
#                                                                      #
########################################################################

import functools
import logging
import struct

from .codes import (
    AIR_STATUS,
    BASE_TESTS,
    COMPRESSION_TESTS,
    DTC,
    FUEL_STATUS,
    FUEL_TYPES,
    IGNITION_TYPE,
    OBD_COMPLIANCE,
    SPARK_TESTS,
    TEST_IDS,
)
from .OBDResponse import Monitor, MonitorTest, Status, StatusTest
from .UnitsAndScaling import UAS_IDS, Unit
from .utils import BitArray, bytes_to_hex, bytes_to_int, twos_comp

logger = logging.getLogger(__name__)

"""
All decoders take the form:

def <name>(<list_of_messages>):
    ...
    return <value>

"""


# drop all messages, return None
def drop(_):
    """Drop all messages, return None."""
    return None


# data in, data out
def noop(messages):
    """Get Data in, data out."""
    return messages[0].data


# hex in, bitstring out
def pid(messages):
    """Hex in, bitstring out."""
    d = messages[0].data[2:]
    return BitArray(d)


# returns the raw strings from the ELM
def raw_string(messages):
    """Return the raw strings from the ELM."""
    return "\n".join([m.raw() for m in messages])


# Some decoders are simple and are already implemented in the Units And Scaling
# tables (used mainly for Mode 06). The uas() decoder is a wrapper for any
# Unit/Scaling in that table, simply to avoid redundant code.


def uas(id_):
    """Get the corresponding decoder for this UAS ID."""
    return functools.partial(decode_uas, id_=id_)


def decode_uas(messages, id_):
    """Chop off mode and PID bytes."""
    d = messages[0].data[2:]  # chop off mode and PID bytes
    return UAS_IDS[id_](d)


# General sensor decoders
# Return pint Quantities


def count(messages):
    """Count messages."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    return v * Unit.count


# 0 to 100 %
def percent(messages):
    """Calculate percent 0 to 100%."""
    d = messages[0].data[2:]
    v = d[0]
    v = v * 100.0 / 255.0
    return v * Unit.percent


# -100 to 100 %
def percent_centered(messages):
    """Calculate percent -1000 to 100%."""
    d = messages[0].data[2:]
    v = d[0]
    v = (v - 128) * 100.0 / 128.0
    return v * Unit.percent


# -40 to 215 C
def temp(messages):
    """Calculate temperature."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v = v - 40
    return Unit.Quantity(v, Unit.celsius)  # non-multiplicative unit


# -128 to 128 mA
def current_centered(messages):
    """Calculate current."""
    d = messages[0].data[2:]
    v = bytes_to_int(d[2:4])
    v = (v / 256.0) - 128
    return v * Unit.milliampere


# 0 to 1.275 volts
def sensor_voltage(messages):
    """Calculate voltage 0 to 1.275 volts."""
    d = messages[0].data[2:]
    v = d[0] / 200.0
    return v * Unit.volt


# 0 to 8 volts
def sensor_voltage_big(messages):
    """Calculate voltage 0 to 8 volts."""
    d = messages[0].data[2:]
    v = bytes_to_int(d[2:4])
    v = (v * 8.0) / 65535
    return v * Unit.volt


# 0 to 765 kPa
def fuel_pressure(messages):
    """Calculate fuel pressure 0 to 765 kPa."""
    d = messages[0].data[2:]
    v = d[0]
    v = v * 3
    return v * Unit.kilopascal


# 0 to 255 kPa
def pressure(messages):
    """Calculate pressure 0 to 255 kPa."""
    d = messages[0].data[2:]
    v = d[0]
    return v * Unit.kilopascal


# -8192 to 8192 Pa
def evap_pressure(messages):
    """Calculate pressure -8192 to 8192 Pa."""
    # decode the twos complement
    d = messages[0].data[2:]
    a = twos_comp(d[0], 8)
    b = twos_comp(d[1], 8)
    v = ((a * 256.0) + b) / 4.0
    return v * Unit.pascal


# 0 to 327.675 kPa
def abs_evap_pressure(messages):
    """Calculate pressure 0 to 327.675 kPa."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v = v / 200.0
    return v * Unit.kilopascal


# -32767 to 32768 Pa
def evap_pressure_alt(messages):
    """Calculate pressure -32767 to 32768 Pa."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v = v - 32767
    return v * Unit.pascal


# -64 to 63.5 degrees
def timing_advance(messages):
    """Calculate timing advance -64 to 63.5 degree."""
    d = messages[0].data[2:]
    v = d[0]
    v = (v - 128) / 2.0
    return v * Unit.degree


# -210 to 301 degrees
def inject_timing(messages):
    """Calculate inject timing -210 to 301 degrees."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v = (v - 26880) / 128.0
    return v * Unit.degree


# 0 to 2550 grams/sec
def max_maf(messages):
    """Calculate max maf 0 to 2550 grams/sec."""
    d = messages[0].data[2:]
    v = d[0]
    v = v * 10
    return v * Unit.gps


# 0 to 3212 Liters/hour
def fuel_rate(messages):
    """Calculate fuel rate 0 to 3212 Liters/hour."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v = v * 0.05
    return v * Unit.liters_per_hour


# special bit encoding for PID 13
def o2_sensors(messages):
    """Calculate o2 sensors."""
    d = messages[0].data[2:]
    bits = BitArray(d)
    return (
        (),  # bank 0 is invalid
        tuple(bits[:4]),  # bank 1
        tuple(bits[4:]),  # bank 2
    )


def aux_input_status(messages):
    """Return aux input status."""
    d = messages[0].data[2:]
    return ((d[0] >> 7) & 1) == 1  # first bit indicate PTO status


# special bit encoding for PID 1D
def o2_sensors_alt(messages):
    """Calculate o2 sensors."""
    d = messages[0].data[2:]
    bits = BitArray(d)
    return (
        (),  # bank 0 is invalid
        tuple(bits[:2]),  # bank 1
        tuple(bits[2:4]),  # bank 2
        tuple(bits[4:6]),  # bank 3
        tuple(bits[6:]),  # bank 4
    )


# 0 to 25700 %
def absolute_load(messages):
    """Calculate absolute load 0 to 25700 %."""
    d = messages[0].data[2:]
    v = bytes_to_int(d)
    v *= 100.0 / 255.0
    return v * Unit.percent


def elm_voltage(messages):
    """Calculate ELM dongle voltage."""
    # doesn't register as a normal OBD response,
    # so access the raw frame data
    v = messages[0].frames[0].raw
    # Some ELMs provide float V (for example messages[0].frames[0].raw => u'12.3V'
    v = v.lower()
    v = v.replace("v", "")

    try:
        return float(v) * Unit.volt
    except ValueError:
        logger.warning("Failed to parse ELM voltage")
        return None


# Special decoders
# Return objects, lists, etc


def status(messages):
    """Decode status message."""
    d = messages[0].data[2:]
    bits = BitArray(d)

    #            ┌Components not ready
    #            |┌Fuel not ready
    #            ||┌Misfire not ready
    #            |||┌Spark vs. Compression
    #            ||||┌Components supported
    #            |||||┌Fuel supported
    #  ┌MIL      ||||||┌Misfire supported
    #  |         |||||||
    #  10000011 00000111 11111111 00000000
    #   [# DTC] X        [supprt] [~ready]

    output = Status()
    output.MIL = bits[0]
    output.DTC_count = bits.value(1, 8)
    output.ignition_type = IGNITION_TYPE[int(bits[12])]

    # load the 3 base tests that are always present
    for i, name in enumerate(BASE_TESTS[::-1]):
        t = StatusTest(name, bits[13 + i], not bits[9 + i])
        output.__dict__[name] = t

    # different tests for different ignition types
    if bits[12]:  # compression
        for i, name in enumerate(
            COMPRESSION_TESTS[::-1]
        ):  # reverse to correct for bit vs. indexing order
            t = StatusTest(name, bits[(2 * 8) + i], not bits[(3 * 8) + i])
            output.__dict__[name] = t

    else:  # spark
        for i, name in enumerate(
            SPARK_TESTS[::-1]
        ):  # reverse to correct for bit vs. indexing order
            t = StatusTest(name, bits[(2 * 8) + i], not bits[(3 * 8) + i])
            output.__dict__[name] = t

    return output


def fuel_status(messages):
    """Decode fuel status."""
    d = messages[0].data[2:]
    bits = BitArray(d)

    status_1 = ""
    status_2 = ""

    if bits[0:8].count(True) == 1:
        if 7 - bits[0:8].index(True) < len(FUEL_STATUS):
            status_1 = FUEL_STATUS[7 - bits[0:8].index(True)]
        else:
            logger.debug("Invalid response for fuel status (high bits set)")
    else:
        logger.debug("Invalid response for fuel status (multiple/no bits set)")

    if bits[8:16].count(True) == 1:
        if 7 - bits[8:16].index(True) < len(FUEL_STATUS):
            status_2 = FUEL_STATUS[7 - bits[8:16].index(True)]
        else:
            logger.debug("Invalid response for fuel status (high bits set)")
    else:
        logger.debug("Invalid response for fuel status (multiple/no bits set)")

    if not status_1 and not status_2:
        return None
    return (status_1, status_2)


def air_status(messages):
    """Decode air status."""
    d = messages[0].data[2:]
    bits = BitArray(d)

    st = None
    if bits.num_set() == 1:
        st = AIR_STATUS[7 - bits[0:8].index(True)]
    else:
        logger.debug("Invalid response for fuel status (multiple/no bits set)")

    return st


def obd_compliance(messages):
    """Decode OBD compliance."""
    d = messages[0].data[2:]
    i = d[0]

    v = None

    if i < len(OBD_COMPLIANCE):
        v = OBD_COMPLIANCE[i]
    else:
        logger.debug("Invalid response for OBD compliance (no table entry)")

    return v


def fuel_type(messages):
    """Decode fuel type."""
    d = messages[0].data[2:]
    i = d[0]  # todo, support second fuel system

    v = None

    if i < len(FUEL_TYPES):
        v = FUEL_TYPES[i]
    else:
        logger.debug("Invalid response for fuel type (no table entry)")

    return v


def parse_dtc(_bytes):
    """Convert 2 bytes into a DTC code."""

    # check validity (also ignores padding that the ELM returns)
    if (len(_bytes) != 2) or (_bytes == (0, 0)):
        return None

    # BYTES: (16,      35      )
    # HEX:    4   1    2   3
    # BIN:    01000001 00100011
    #         [][][  in hex   ]
    #         | / /
    # DTC:    C0123

    _dtc = ["P", "C", "B", "U"][_bytes[0] >> 6]  # the last 2 bits of the first byte
    _dtc += str(
        (_bytes[0] >> 4) & 0b0011
    )  # the next pair of 2 bits. Mask off the bits we read above
    _dtc += bytes_to_hex(_bytes)[1:4]

    # pull a description if we have one
    return (_dtc, DTC.get(_dtc, ""))


def single_dtc(messages):
    """Parse a single DTC from a message."""
    d = messages[0].data[2:]
    return parse_dtc(d)


def dtc(messages):
    """Convert a frame of 2-byte DTCs into a list of DTCs."""
    codes = []
    d = []
    for message in messages:
        d += message.data[2:]  # remove the mode and DTC_count bytes

    # look at data in pairs of bytes
    # looping through ENDING indices to avoid odd (invalid) code lengths
    for n in range(1, len(d), 2):
        # parse the code
        _dtc = parse_dtc((d[n - 1], d[n]))

        if _dtc is not None:
            codes.append(_dtc)

    return codes


def parse_monitor_test(d, mon):
    """Parse monitor test."""
    test = MonitorTest()

    tid = d[1]

    if tid in TEST_IDS:
        test.name = TEST_IDS[tid][0]  # lookup the name from the table
        test.desc = TEST_IDS[tid][1]  # lookup the description from the table
    else:
        logger.debug("Encountered unknown Test ID")
        test.name = "Unknown"
        test.desc = "Unknown"

    u = UAS_IDS.get(d[2], None)

    # if we can't decode the value, abort
    if u is None:
        logger.debug("Encountered unknown Units and Scaling ID")
        return None

    # load the test results
    test.tid = tid
    test.value = u(d[3:5])  # convert bytes to actual values
    test.min = u(d[5:7])
    test.max = u(d[7:])

    return test


def monitor(messages):
    """Do monitoring."""
    d = messages[0].data[1:]
    # only dispose of the mode byte. Leave the MID
    # even though we never use the MID byte, it may
    # show up multiple times. Thus, keeping it make
    # for easier parsing.
    mon = Monitor()

    # test that we got the right number of bytes
    extra_bytes = len(d) % 9

    if extra_bytes != 0:
        logger.debug(
            "Encountered monitor message with non-multiple of 9 bytes. Truncating..."
        )
        d = d[: len(d) - extra_bytes]

    # look at data in blocks of 9 bytes (one test result)
    for n in range(0, len(d), 9):
        # extract the 9 byte block, and parse a new MonitorTest
        test = parse_monitor_test(d[n : n + 9], mon)
        if test is not None:
            mon.add_test(test)

    return mon


def encoded_string(length):
    """Extract an encoded string from multi-part messages."""
    return functools.partial(decode_encoded_string, length=length)


def decode_encoded_string(messages, length):
    """Decode encoded string."""
    d = messages[0].data[2:]

    if len(d) < length:
        logger.debug("Invalid string %s. Discarding...", d)
        return None

    # Encoded strings come in bundles of messages with leading null values to
    # pad out the string to the next full message size. We strip off the
    # leading null characters here and return the resulting string.
    return d.strip().strip(b"\x00" b"\x01" b"\x02" b"\\x00" b"\\x01" b"\\x02")


def cvn(messages):
    """Do something."""
    d = decode_encoded_string(messages, 4)
    if d is None:
        return None
    return bytes_to_hex(d)


def unknown(messages):
    """Decode unknown messages."""
    return None


def power_switch(messages):
    """Decode power switch messages."""
    d = messages[0].data  # only operate on a single message
    v = d[4] & 0x80 == 0x80
    return {"power_switch": v}


def gear_position(messages):
    """Decode gear position messages."""
    d = messages[0].data  # only operate on a single message
    match d[3]:
        case 1:
            v = "Park"
        case 2:
            v = "Reverse"
        case 3:
            v = "Neutral"
        case 4:
            v = "Drive"
        case 5:
            v = "Eco"
        case _:
            v = "Unknown"

    return {"gear_position": v}


def bat_12v_voltage(messages):
    """Decode 12V battery voltage messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 0.08
    return {"bat_12v_voltage": v}


def bat_12v_current(messages):
    """Decode 12V battery current messages."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0] / 256
    return {"bat_12v_current": v}


def quick_charges(messages):
    """Decode Number of quick charges messages."""
    d = messages[0].data  # only operate on a single message
    v = int.from_bytes(d[3:5])
    return {"quick_charges": v}


def l1_l2_charges(messages):
    """Decode Number of L1/L2 charges messages."""
    d = messages[0].data  # only operate on a single message
    v = int.from_bytes(d[3:5])
    return {"l1_l2_charges": v}


def ambient_temp(messages):
    """Decode ambient temperature messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] / 2 - 40
    return {"ambient_temp": v}


def estimated_ac_power(messages):
    """Decode estimated AC power messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 50
    return {"estimated_ac_power": v}


def estimated_ptc_power(messages):
    """Decode estimated PTC power messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 250
    return {"estimated_ptc_power": v}


def aux_power(messages):
    """Decode Auxiliary equipment power messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 100
    return {"aux_power": v}


def ac_power(messages):
    """Decode AC system power messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 250
    return {"ac_power": v}


def plug_state(messages):
    """Decode Plug state of J1772 socket messages."""
    d = messages[0].data  # only operate on a single message
    match d[3]:
        case 0:
            v = "Not plugged"
        case 1:
            v = "Partial plugged"
        case 2:
            v = "Plugged"
        case _:
            v = "Unknown"
    return {"plug_state": v}


def charge_mode(messages):
    """Decode Charging mode messages."""
    d = messages[0].data  # only operate on a single message
    match d[3]:
        case 0:
            v = "Not charging"
        case 1:
            v = "L1 charging"
        case 2:
            v = "L2 charging"
        case 3:
            v = "L3 charging"
        case _:
            v = "Unknown"
    return {"charge_mode": v}


def rpm(messages):
    """Decode Motor RPM messages."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0]
    return {"rpm": v}


def obc_out_power(messages):
    """Decode On-board charger output power messages (W)."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0] * 100
    return {"obc_out_power": v}


def motor_power(messages):
    """Decode Traction motor power messages (W)."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0] * 40
    return {"motor_power": v}


def speed(messages):
    """Decode Vehicle speed messages (km/h)."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0] / 10
    return {"speed": v}


def ac_on(messages):
    """Decode AC status messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] == 0x01
    return {"ac_on": v}


def rear_heater(messages):
    """Decode Rear heater status messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] == 0xA2
    return {"rear_heater": v}


def eco_mode(messages):
    """Decode ECO mode status messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] == 0x10 | d[3] == 0x11
    return {"eco_mode": v}


def e_pedal_mode(messages):
    """Decode e-Pedal mode status messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] == 0x04
    return {"e_pedal_mode": v}


def odometer(messages):
    """Decode Total odometer reading (km) messages."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!i", bytearray([0x00]) + d[3:6])[0] / 10
    return {"odometer": v}


def tp_fr(messages):
    """Decode Tyre pressure front right (kPa) messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 1.7236894
    return {"tp_fr": v}


def tp_fl(messages):
    """Decode Tyre pressure front left (kPa) messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 1.7236894
    return {"tp_fl": v}


def tp_rr(messages):
    """Decode Tyre pressure rear right (kPa) messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 1.7236894
    return {"tp_rr": v}


def tp_rl(messages):
    """Decode Tyre pressure rear left (kPa) messages."""
    d = messages[0].data  # only operate on a single message
    v = d[3] * 1.7236894
    return {"tp_rl": v}


def range_remaining(messages):
    """Decode Remaining range (km) messages."""
    d = messages[0].data  # only operate on a single message
    v = struct.unpack("!h", d[3:5])[0] / 10
    return {"range_remaining": v}


def lbc(messages):
    """Decode LBC message."""
    d = messages[0].data
    if len(d) == 0:
        return None
    hv_battery_current_1 = int.from_bytes(d[2:6], byteorder="big", signed=False)
    hv_battery_current_2 = int.from_bytes(d[8:12], byteorder="big", signed=False)
    if hv_battery_current_1 & 0x8000000 == 0x8000000:
        hv_battery_current_1 = hv_battery_current_1 | -0x100000000
    if hv_battery_current_2 & 0x8000000 == 0x8000000:
        hv_battery_current_2 = hv_battery_current_2 | -0x100000000
    return {
        "state_of_charge": int.from_bytes(d[33:36]) / 10000,
        "hv_battery_health": int.from_bytes(d[30:32]) / 102.4,
        "hv_battery_Ah": int.from_bytes(d[37:40]) / 10000,
        "hv_battery_current_1": hv_battery_current_1 / 1024,
        "hv_battery_current_2": hv_battery_current_2 / 1024,
        "hv_battery_voltage": int.from_bytes(d[20:22]) / 100,
    }
