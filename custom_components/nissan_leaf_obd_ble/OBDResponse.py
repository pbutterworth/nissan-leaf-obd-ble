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
# OBDResponse.py                                                       #
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
import sys
import time

from .codes import BASE_TESTS, COMPRESSION_TESTS, SPARK_TESTS, TEST_IDS

logger = logging.getLogger(__name__)

if sys.version[0] < "3":
    string_types = (str, unicode)
else:
    string_types = (str,)


class OBDResponse:
    """Standard response object for any OBDCommand."""

    def __init__(self, command=None, messages=None) -> None:
        """Initialise."""
        self.command = command
        self.messages = messages if messages else []
        self.value = None
        self.time = time.time()

    @property
    def unit(self):
        """Return unit."""
        # for backwards compatibility
        from obd import Unit  # local import to avoid cyclic-dependency

        if isinstance(self.value, Unit.Quantity):
            return str(self.value.u)
        if self.value is None:
            return None
        return str(type(self.value))

    def is_null(self):
        """Return whether this is null."""
        return (not self.messages) or (self.value is None)

    def __str__(self):
        """Render string representation."""
        return str(self.value)

    # Special value types used in OBDResponses
    # instantiated in decoders.py


class Status:
    """Status object."""

    def __init__(self) -> None:
        """Initialise."""
        self.MIL = False
        self.DTC_count = 0
        self.ignition_type = ""

        # make sure each test is available by name
        # until real data comes it. This also prevents things from
        # breaking when the user looks up a standard test that's null.
        null_test = StatusTest()
        for name in BASE_TESTS + SPARK_TESTS + COMPRESSION_TESTS:
            if name:  # filter out None/reserved tests
                self.__dict__[name] = null_test


class StatusTest:
    """Test status class."""

    def __init__(self, name="", available=False, complete=False) -> None:
        """Initialise."""
        self.name = name
        self.available = available
        self.complete = complete

    def __str__(self):
        """Return string representation."""
        a = "Available" if self.available else "Unavailable"
        c = "Complete" if self.complete else "Incomplete"
        return f"Test {self.name}: {a}, {c}"


class Monitor:
    """Monitor class."""

    def __init__(self) -> None:
        """Initialise."""
        self._tests = {}  # tid : MonitorTest

        # make the standard TIDs available as null monitor tests
        # until real data comes it. This also prevents things from
        # breaking when the user looks up a standard test that's null.
        null_test = MonitorTest()

        for tid in TEST_IDS:
            name = TEST_IDS[tid][0]
            self.__dict__[name] = null_test
            self._tests[tid] = null_test

    def add_test(self, test):
        """Add a test."""
        self._tests[test.tid] = test
        if test.name is not None:
            self.__dict__[test.name] = test

    @property
    def tests(self):
        """Return tests."""
        return [test for test in self._tests.values() if not test.is_null()]

    def __str__(self):
        """Return string representation."""
        if len(self.tests) > 0:
            return "\n".join([str(t) for t in self.tests])
        return "No tests to report"

    def __len__(self):
        """Return length."""
        return len(self.tests)

    def __getitem__(self, key):
        """Get item."""
        if isinstance(key, int):
            return self._tests.get(key, MonitorTest())
        if isinstance(key, string_types):
            return self.__dict__.get(key, MonitorTest())
        logger.warning(
            "Monitor test results can only be retrieved by TID value or property name"
        )


class MonitorTest:
    """Monitor test class."""

    def __init__(self) -> None:
        """Initialise."""
        self.tid = None
        self.name = None
        self.desc = None
        self.value = None
        self.min = None
        self.max = None

    @property
    def passed(self):
        """Return passed."""
        if not self.is_null():
            return (self.value >= self.min) and (self.value <= self.max)
        return False

    def is_null(self):
        """Return if null."""
        return (
            self.tid is None
            or self.value is None
            or self.min is None
            or self.max is None
        )

    def __str__(self):
        """Return string representation."""
        return "{} : {} [{}]".format(
            self.desc,
            str(self.value),
            "PASSED" if self.passed else "FAILED",
        )
