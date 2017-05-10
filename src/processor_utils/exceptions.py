# -*- coding: utf-8 -*-

"""processor loading exceptions"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# file:         exceptions.py
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


class BlockedCapError(RuntimeError):

    """Blocked Input capability error

    A blocked input capability is one that if fed to a supporting input
    port won't reach all outputs with the full width of the input it was
    fed to.

    """

    # parameter indices in format message
    CAPABILITY_IDX = 0

    PORT_IDX = 1

    CAPACITY_IDX = 2

    MAX_WIDTH_IDX = 3

    def __init__(self, msg_tmpl, blocking_info, max_width):
        """Create a blocked input capability error.

        `self` is this blocked input capability error.
        `msg_tmpl` is the error format message taking in order the
                   capability, port, actual, and maximum bus widths as
                   positional parameters.
        `blocking_info` is the blocking information.
        `max_width` is the maximum capacity that can flow from the port
                    to the outputs.

        """
        RuntimeError.__init__(
            self, msg_tmpl.format(blocking_info.capability, blocking_info.port,
                                  blocking_info.capacity, max_width))
        self._capability = blocking_info.capability
        self._port = blocking_info.port
        self._capacity = blocking_info.capacity
        self._max_width = max_width

    @property
    def capability(self):
        """Blocked capability

        `self` is this blocked input capability error.

        """
        return self._capability

    @property
    def capacity(self):
        """Capacity of the blocked port

        `self` is this blocked input capability error.

        """
        return self._capacity

    @property
    def max_width(self):
        """Maximum allowed width

        `self` is this blocked input capability error.

        """
        return self._max_width

    @property
    def port(self):
        """Port the capability is block at

        `self` is this blocked input capability error.

        """
        return self._port


class CapPortInfo(object):

    """Capability-port combination information"""

    def __init__(self, capability, port, capacity):
        """Set the capability-port combination information.

        `self` is this capability-port combination information.
        `capability` is the capability.
        `port` is the port.
        `capacity` is the port width.

        """
        self._capability = capability
        self._port = port
        self._capacity = capacity

    @property
    def capability(self):
        """Capability

        `self` is this capability-port combination information.

        """
        return self._capability

    @property
    def capacity(self):
        """Port width

        `self` is this capability-port combination information.

        """
        return self._capacity

    @property
    def port(self):
        """Port

        `self` is this capability-port combination information.

        """
        return self._port


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
        `port` is the blocked input error.

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

    # parameter indices in format message
    OLD_ELEM_IDX = 0

    NEW_ELEM_IDX = 1

    def __init__(self, msg_tmpl, old_elem, new_elem):
        """Create a duplicate element error.

        `self` is this duplicate element error.
        `msg_tmpl` is the error format message taking in order the old
                   and new elements as positional parameters.
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


class EmptyProcError(RuntimeError):

    """Empty processor error"""


class TightWidthError(RuntimeError):

    """Tight bus width error"""

    # parameter indices in format message
    REAL_WIDTH_IDX = 0

    MIN_WIDTH_IDX = 1

    def __init__(self, msg_tmpl, actual_width, min_width):
        """Create a tight bus width error.

        `self` is this width error.
        `msg_tmpl` is the error format message taking in order the
                   actual and minimum bus widths as positional
                   parameters.
        `actual_width` is the violating width value.
        `min_width` is the minimum allowed width.

        """
        RuntimeError.__init__(self, msg_tmpl.format(actual_width, min_width))
        self._actual_width = actual_width
        self._min_width = min_width

    @property
    def actual_width(self):
        """Violating width

        `self` is this tight bus width error.

        """
        return self._actual_width

    @property
    def min_width(self):
        """Minimum allowed width

        `self` is this tight bus width error.

        """
        return self._min_width


class UndefElemError(RuntimeError):

    """Unknown set element error"""

    def __init__(self, msg_tmpl, elem):
        """Create an unknown element error.

        `self` is this unknown element error.
        `msg_tmpl` is the error format message taking the unknown
                   element as a positional argument.
        `elem` is the unknown element.

        """
        RuntimeError.__init__(self, msg_tmpl.format(elem))
        self._elem = elem

    @property
    def element(self):
        """Unknown element

        `self` is this unknown element error.

        """
        return self._elem
