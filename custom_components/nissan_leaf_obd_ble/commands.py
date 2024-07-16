"""Define command tables."""

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
# commands.py                                                          #
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

import logging

from .decoders import (
    ac_on,
    ac_power,
    ambient_temp,
    aux_power,
    bat_12v_current,
    bat_12v_voltage,
    charge_mode,
    e_pedal_mode,
    eco_mode,
    estimated_ac_power,
    estimated_ptc_power,
    gear_position,
    l1_l2_charges,
    lbc,
    motor_power,
    obc_out_power,
    odometer,
    plug_state,
    power_switch,
    quick_charges,
    range_remaining,
    rear_heater,
    rpm,
    speed,
    tp_fl,
    tp_fr,
    tp_rl,
    tp_rr,
    unknown,
)
from .OBDCommand import OBDCommand

logger = logging.getLogger(__name__)


# NOTE: the NAME field will be used as the dict key for that sensor
# NOTE: commands MUST be in PID order, one command per PID (for fast lookup using __mode1__[pid])

# see OBDCommand.py for descriptions & purposes for each of these fields

# fmt: off
leaf_commands = {
    #          name                     description                     cmd             bytes decoder               header
    "unknown":               OBDCommand("unknown",               "Mystery command",              b"0210C0",      0,  unknown,                header=b"797",),
    "power_switch":          OBDCommand("power_switch",          "Power switch status",          b"03221304",    5,  power_switch,           header=b"797",),
    "gear_position":         OBDCommand("gear_position",         "Gear position",                b"03221156",    4,  gear_position,          header=b"797",),
    "bat_12v_voltage":       OBDCommand("bat_12v_voltage",       "12V battery voltage",          b"03221103",    4,  bat_12v_voltage,        header=b"797",),
    "bat_12v_current":       OBDCommand("bat_12v_current",       "12V battery current",          b"03221183",    5,  bat_12v_current,        header=b"797",),
    "quick_charges":         OBDCommand("quick_charges",         "Number of quick charges",      b"03221203",    5,  quick_charges,          header=b"797",),
    "l1_l2_charges":         OBDCommand("l1_l2_charges",         "Number of L1/L2 charges",      b"03221205",    5,  l1_l2_charges,          header=b"797",),
    "ambient_temp":          OBDCommand("ambient_temp",          "Ambient temperature",          b"0322115d",    4,  ambient_temp,           header=b"797",),
    "estimated_ac_power":    OBDCommand("estimated_ac_power",    "Estimated AC system power",    b"03221261",    4,  estimated_ac_power,     header=b"797",),
    "estimated_ptc_power":   OBDCommand("estimated_ptc_power",   "Estimated PTC system power",   b"03221262",    4,  estimated_ptc_power,    header=b"797",),
    "aux_power":             OBDCommand("aux_power",             "Auxiliary equipment power",    b"03221152",    4,  aux_power,              header=b"797",),
    "ac_power":              OBDCommand("ac_power",              "AC system power",              b"03221151",    4,  ac_power,               header=b"797",),
    "plug_state":            OBDCommand("plug_state",            "Plug state of J1772 socket",   b"03221234",    4,  plug_state,             header=b"797",),
    "charge_mode":           OBDCommand("charge_mode",           "Charging mode",                b"0322114e",    4,  charge_mode,            header=b"797",),
    "rpm":                   OBDCommand("rpm",                   "Motor RPM",                    b"03221255",    5,  rpm,                    header=b"797",),
    "obc_out_power":         OBDCommand("obc_out_power",         "On-board charger output power",b"03221236",    5,  obc_out_power,          header=b"797",),
    "motor_power":           OBDCommand("motor_power",           "Traction motor power",         b"03221146",    5,  motor_power,            header=b"797",),
    "speed":                 OBDCommand("speed",                 "Vehicle speed",                b"0322121a",    5,  speed,                  header=b"797",),
    "ac_on":                 OBDCommand("ac_on",                 "AC status",                    b"03221106",    5,  ac_on,                  header=b"797",),
    "rear_heater":           OBDCommand("rear_heater",           "Rear heater status",           b"0322110f",    4,  rear_heater,            header=b"797",),
    "eco_mode":              OBDCommand("eco_mode",              "ECO mode status",              b"03221318",    5,  eco_mode,               header=b"797",),
    "e_pedal_mode":          OBDCommand("e_pedal_mode",          "e-Pedal mode status",          b"0322131A",    5,  e_pedal_mode,           header=b"797",),

    "odometer":              OBDCommand("odometer",              "Total odometer reading (km)",  b"03220e01",    6,  odometer,               header=b"743",),
    "tp_fr":                 OBDCommand("tp_fr",                 "Tyre pressure front right",    b"03220e25",    4,  tp_fr,                  header=b"743",),
    "tp_fl":                 OBDCommand("tp_fl",                 "Tyre pressure front left",     b"03220e26",    4,  tp_fl,                  header=b"743",),
    "tp_rr":                 OBDCommand("tp_rr",                 "Tyre pressure rear right",     b"03220e27",    4,  tp_rr,                  header=b"743",),
    "tp_rl":                 OBDCommand("tp_rl",                 "Tyre pressure rear left",      b"03220e28",    4,  tp_rl,                  header=b"743",),
    "range_remaining":       OBDCommand("range_remaining",       "Remaining range (km)",         b"03220e24",    13, range_remaining,        header=b"743",),

    "lbc":                   OBDCommand("lbc",                   "Li-ion battery controller",    b"022101",      53, lbc,                    header=b"79B",),
}
# fmt: on
