"""The main API for talking to the OBD BLE module."""

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
# obd.py                                                               #
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

from bleak.backends.device import BLEDevice

# from .commands import commands
from .elm327 import ELM327, OBDStatus
from .OBDResponse import OBDResponse

logger = logging.getLogger(__name__)


class OBD:
    """Class representing an OBD-II connection with it's assorted commands/sensors."""

    def __init__(
        self,
        device: BLEDevice,
        fast=True,
        timeout=0.1,
    ) -> None:
        """Initialise."""
        self.interface = None
        self.fast = fast  # global switch for disabling optimizations
        self.timeout = timeout
        self.__device = device
        self.__last_header = ()  # for comparing with the previously used header
        self.__frame_counts = {}  # keeps track of the number of return frames for each command

    @classmethod
    async def create(
        cls,
        device: BLEDevice,
        protocol=None,
        fast=True,
        timeout=0.1,
        check_voltage=True,
        start_low_power=False,
    ):
        """Manufacture instance."""
        self = cls(device, fast, timeout)

        logger.debug("Connecting to BLEDevice")
        await self.__connect(
            protocol, check_voltage, start_low_power
        )  # initialize by connecting and loading sensors
        return self

    async def __connect(self, protocol, check_voltage, start_low_power):
        """Attempt to instantiate an ELM327 connection object."""

        self.interface = await ELM327.create(
            self.__device, protocol, self.timeout, check_voltage, start_low_power
        )

        # if the connection failed, close it
        if self.status() == OBDStatus.NOT_CONNECTED:
            # the ELM327 class will report its own errors
            await self.close()

    async def __set_header(self, header) -> None:
        if header == self.__last_header:
            return
        r = await self.interface.send_and_parse(b"AT SH " + header + b" ")
        if not r:
            logger.info("Set Header ('AT SH %s') did not return data", header)
            return
        if "\n".join([m.raw() for m in r]) != "OK":
            logger.info("Set Header ('AT SH %s') did not return 'OK'", header)
            return

        r = await self.interface.send_and_parse(b"AT FC SH " + header + b" ")
        if not r:
            logger.info("Set Header ('AT FC SH %s') did not return data", header)
            return
        if "\n".join([m.raw() for m in r]) != "OK":
            logger.info("Set Header ('AT FC SH %s') did not return 'OK'", header)
            return

        r = await self.interface.send_and_parse(b"AT FC SD 30 00 00")
        if not r:
            logger.info("Set Header ('AT FC SD %s') did not return data", header)
            return
        if "\n".join([m.raw() for m in r]) != "OK":
            logger.info("Set Header ('AT FC SD %s') did not return 'OK'", header)
            return

        r = await self.interface.send_and_parse(b"AT FC SM 1")
        if not r:
            logger.info("Set Header ('AT FC SM %s') did not return data", header)
            return
        if "\n".join([m.raw() for m in r]) != "OK":
            logger.info("Set Header ('AT FC SM %s') did not return 'OK'", header)
            return

        self.__last_header = header

    async def close(self):
        """Close the connection, and clears supported_commands."""

        if self.interface is not None:
            logger.info("Closing connection")
            await self.interface.close()
            self.interface = None

    def status(self):
        """Return the OBD connection status."""
        if self.interface is None:
            return OBDStatus.NOT_CONNECTED
        return self.interface.status()

    async def low_power(self):
        """Enter low power mode."""
        if self.interface is None:
            return OBDStatus.NOT_CONNECTED
        return await self.interface.low_power()

    async def normal_power(self):
        """Exit low power mode."""
        if self.interface is None:
            return OBDStatus.NOT_CONNECTED
        return await self.interface.normal_power()

    def protocol_name(self):
        """Return the name of the protocol being used by the ELM327."""
        if self.interface is None:
            return ""
        return self.interface.protocol_name()

    def protocol_id(self):
        """Return the ID of the protocol being used by the ELM327."""
        if self.interface is None:
            return ""
        return self.interface.protocol_id()

    def is_connected(self):
        """Return. a boolean for whether a connection with the car was made.

        Note: this function returns False when:
        obd.status = OBDStatus.ELM_CONNECTED
        """
        return self.status() == OBDStatus.CAR_CONNECTED

    async def query(self, cmd, force=False):
        """Primary API function. Send commands to the car, and protect against sending unsupported commands."""

        if self.status() == OBDStatus.NOT_CONNECTED:
            logger.warning("Query failed, no connection available")
            return OBDResponse()

        # if the user forces, skip all checks
        if not force and not self.test_cmd(cmd):
            return OBDResponse()

        await self.__set_header(cmd.header)

        logger.info("Sending command: %s", cmd)
        cmd_string = self.__build_command_string(cmd)
        messages = await self.interface.send_and_parse(cmd_string)
        for f in messages[0].frames:
            logger.debug("Received frame: %s", f.raw)

        # if we don't already know how many frames this command returns,
        # log it, so we can specify it next time
        if cmd not in self.__frame_counts:
            self.__frame_counts[cmd] = sum([len(m.frames) for m in messages])

        if not messages:
            logger.info("No valid OBD Messages returned")
            return OBDResponse()

        for m in messages:
            if len(m.data) == 0 & ((m.raw == "NO DATA") | (m.raw == "CAN ERROR")):
                logger.info("Vehicle not responding")
                return OBDResponse()

        return cmd(messages)  # compute a response object

    def __build_command_string(self, cmd):
        """Assemble the appropriate command string."""
        cmd_string = cmd.command

        # if we know the number of frames that this command returns,
        # only wait for exactly that number. This avoids some harsh
        # timeouts from the ELM, thus speeding up queries.
        if self.fast and cmd.fast and (cmd in self.__frame_counts):
            cmd_string += str(self.__frame_counts[cmd]).encode()

        return cmd_string
