# -*- coding: utf-8 -*-

"""processor loading exceptions"""

############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
# This file is part of processorSim.
#
# processorSim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# processorSim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with processorSim.  If not, see
# <http://www.gnu.org/licenses/>.
#
# program:      processor simulator
#
# file:         exception.py
#
# function:     processor description loading exceptions
#
# description:  contains exception classes for loading processor
#               descriptions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 26 (Twenty Six)
#               Komodo IDE, version 11.1.1 build 91089, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################


class BadEdgeError(RuntimeError):

    """Bad edge error"""

    def __init__(self, msg_tmpl, edge):
        """Create a bad edge error.

        `self` is this bad edge error.
        `msg_tmpl` is the error format message taking the bad edge as a
                   positional argument.
        `edge` is the bad edge.

        """
        RuntimeError.__init__(self, msg_tmpl.format(edge))
        self._edge = edge

    @property
    def edge(self):
        """Bad edge

        `self` is this bad edge error.

        """
        return self._edge


class BadWidthError(RuntimeError):

    """Bad Width error

    A unit width is bad if it isn't positive.

    """

    def __init__(self, msg_tmpl, unit, width):
        """Create a bad width error.

        `self` is this bad width error.
        `msg_tmpl` is the error format message taking in order the
                   offending unit and width as positional arguments.
        `unit` is the unit with a bad width.
        `width` is the bad width.

        """
        RuntimeError.__init__(self, msg_tmpl.format(unit, width))
        self._unit = unit
        self._width = width

    @property
    def unit(self):
        """Unit having the bad width

        `self` is this bad width error.

        """
        return self._unit

    @property
    def width(self):
        """Bad width

        `self` is this bad width error.

        """
        return self._width

    # parameter indices in format message
    UNIT_IDX = 0

    WIDTH_IDX = 1


class BlockedCapError(RuntimeError):

    """Blocked Input capability error

    A blocked input capability is one that if fed to a supporting input
    port won't reach all outputs with full or partial width from the
    input it was fed to.

    """

    def __init__(self, msg_tmpl, blocking_info):
        """Create a blocked input capability error.

        `self` is this blocked input capability error.
        `msg_tmpl` is the error format message taking in order the
                   capability, port, actual, and maximum bus widths as
                   positional arguments.
        `blocking_info` is the blocking information.

        """
        RuntimeError.__init__(
            self, msg_tmpl.format(blocking_info.capability_info.reporting_name,
                                  blocking_info.port_info.reporting_name))
        self._capability = blocking_info.capability_info.std_name
        self._port = blocking_info.port_info.std_name

    @property
    def capability(self):
        """Blocked capability

        `self` is this blocked input capability error.

        """
        return self._capability

    @property
    def port(self):
        """Port the capability is block at

        `self` is this blocked input capability error.

        """
        return self._port

    # parameter indices in format message
    CAPABILITY_IDX = 0

    PORT_IDX = 1


class CapPortInfo:

    """Capability-port combination information"""

    def __init__(self, capability_info, port_info):
        """Set the capability-port combination information.

        `self` is this capability-port combination information.
        `capability_info` is the capability information.
        `port_info` is the port information.

        """
        self.capability_info = capability_info
        self.port_info = port_info


class ComponentInfo:

    """Component information"""

    def __init__(self, std_name, reporting_name):
        """Set the component information.

        `self` is this component information.
        `std_name` is the component standard name.
        `reporting_name` is the component reporting name.

        """
        self.std_name = std_name
        self.reporting_name = reporting_name


class DeadInputError(RuntimeError):

    """Dead input port error

    A dead input port is one that is connected to units none of which is
    supporting any of the input port capabilities.

    """

    def __init__(self, msg_tmpl, port):
        """Create a dead input error.

        `self` is this dead input error.
        `msg_tmpl` is the error format message taking the blocked port
                   as a positional argument.
        `port` is the blocked input port.

        """
        RuntimeError.__init__(self, msg_tmpl.format(port))
        self._port = port

    @property
    def port(self):
        """Blocked input port

        `self` is this dead input error.

        """
        return self._port


class DupElemError(RuntimeError):

    """Duplicate set element error"""

    def __init__(self, msg_tmpl, old_elem, new_elem):
        """Create a duplicate element error.

        `self` is this duplicate element error.
        `msg_tmpl` is the error format message taking in order the old
                   and new elements as positional arguments.
        `old_elem` is the element already existing.
        `new_elem` is the element just discovered.

        """
        RuntimeError.__init__(self, msg_tmpl.format(old_elem, new_elem))
        self._old_elem = old_elem
        self._new_elem = new_elem

    @property
    def new_element(self):
        """Duplicate element just discovered

        `self` is this duplicate element error.

        """
        return self._new_elem

    @property
    def old_element(self):
        """Element added before

        `self` is this duplicate element error.

        """
        return self._old_elem

    # parameter indices in format message
    OLD_ELEM_IDX = 0

    NEW_ELEM_IDX = 1


class EmptyProcError(RuntimeError):

    """Empty processor error"""
