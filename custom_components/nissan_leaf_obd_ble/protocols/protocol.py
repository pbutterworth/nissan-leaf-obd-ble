"""Part of python-OBD (a derivative of pyOBD)."""
########################################################################
#                                                                      #
# python-OBD: A python OBD-II serial module derived from pyobd         #
#                                                                      #
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)                 #
# Copyright 2009 Secons Ltd. (www.obdtester.com)                       #
# Copyright 2009 Peter J. Creath                                       #
# Copyright 2015 Brendan Whitfield (bcw7044@rit.edu)                   #
#                                                                      #
########################################################################
#                                                                      #
# protocols/protocol.py                                                #
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

from binascii import hexlify
import logging

from ..utils import isHex

logger = logging.getLogger(__name__)

"""

Basic data models for all protocols to use

"""


class Frame:
    """Represent a single parsed line of OBD output."""

    def __init__(self, raw) -> None:
        """Initialise."""
        self.raw = raw
        self.data = bytearray()
        self.priority = None
        self.addr_mode = None
        self.rx_id = None
        self.tx_id = None
        self.type = None
        self.seq_index = 0  # only used when type = CF
        self.data_len = None


class Message:
    """Represent a fully parsed OBD message of one or more Frames (lines)."""

    def __init__(self, frames) -> None:
        """Initialise."""
        self.frames = frames
        self.data = bytearray()

    @property
    def tx_id(self):
        """Return transmit id."""
        if len(self.frames) == 0:
            return None
        return self.frames[0].tx_id

    def hex(self):
        """Return hex representation."""
        return hexlify(self.data)

    def raw(self):
        """Return the original raw input string from the adapter."""
        return "\n".join([f.raw for f in self.frames])

    def parsed(self):
        """Boolean for whether this message was successfully parsed."""
        return bool(self.data)

    def __eq__(self, other):
        """Compare."""
        if isinstance(other, Message):
            for attr in ["frames", "data"]:
                if getattr(self, attr) != getattr(other, attr):
                    return False
            return True
        return False


class Protocol:
    """Protocol objects are factories for Frame and Message objects.

    They are largely stateless, with the exception of an ECU tagging system, which
    is initialized by passing the response to an "0100" command.

    Protocols are __called__ with a list of string responses, and return a
    list of Messages.
    """

    # override in subclass for each protocol

    ELM_NAME = ""  # the ELM's name for this protocol (ie, "SAE J1939 (CAN 29/250)")
    ELM_ID = ""  # the ELM's ID for this protocol (ie, "A")

    def __init__(self) -> None:
        """Construct a protocol object.

        uses a list of raw strings from the
        car to determine the ECU layout.
        """

    def __call__(self, lines):
        """Perform main function.

        accepts a list of raw strings from the car, split by lines
        """

        # ---------------------------- preprocess ----------------------------

        # Non-hex (non-OBD) lines shouldn't go through the big parsers,
        # since they are typically messages such as: "NO DATA", "CAN ERROR",
        # "UNABLE TO CONNECT", etc, so sort them into these two lists:
        obd_lines = []
        non_obd_lines = []

        for line in lines:
            line_no_spaces = line.replace(" ", "")

            if isHex(line_no_spaces):
                obd_lines.append(line_no_spaces)
            else:
                non_obd_lines.append(line)  # pass the original, un-scrubbed line

        # ---------------------- handle valid OBD lines ----------------------

        # parse each frame (each line)
        frames = []
        for line in obd_lines:
            frame = Frame(line)

            # subclass function to parse the lines into Frames
            # drop frames that couldn't be parsed
            if self._parse_frame(frame):
                frames.append(frame)

        # group frames by transmitting ECU
        # frames_by_ECU[tx_id] = [Frame, Frame]
        frames_by_ECU = {}
        for frame in frames:
            if frame.tx_id not in frames_by_ECU:
                frames_by_ECU[frame.tx_id] = [frame]
            else:
                frames_by_ECU[frame.tx_id].append(frame)

        # parse frames into whole messages
        messages = []
        for ecu in sorted(frames_by_ECU.keys()):
            # new message object with a copy of the raw data
            # and frames addressed for this ecu
            message = Message(frames_by_ECU[ecu])

            # subclass function to assemble frames into Messages
            if self._parse_message(message):
                messages.append(message)

        # ----------- handle invalid lines (probably from the ELM) -----------

        for line in non_obd_lines:
            # give each line its own message object
            messages.append(Message([Frame(line)]))
        return messages

    def _parse_frame(self, frame):
        """Override in subclass for each protocol.

        Function recieves a Frame object preloaded
        with the raw string line from the car.

        Function should return a boolean. If fatal errors were
        found, this function should return False, and the Frame will be dropped.
        """
        raise NotImplementedError

    def _parse_message(self, message):
        """Override in subclass for each protocol.

        Function recieves a Message object
        preloaded with a list of Frame objects.

        Function should return a boolean. If fatal errors were
        found, this function should return False, and the Message will be dropped.
        """
        raise NotImplementedError
