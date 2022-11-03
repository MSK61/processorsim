# -*- coding: utf-8 -*-

"""processor loading exceptions"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.73.0, python 3.10.7, Fedora
#               release 36 (Thirty Six)
#
# notes:        This is a private program.
#
############################################################

from string import Template
from typing import Final

import attr

from str_utils import ICaseString


class BadEdgeError(RuntimeError):

    """Bad edge error"""

    def __init__(self, msg_tmpl: str, edge: object) -> None:
        """Create a bad edge error.

        `self` is this bad edge error.
        `msg_tmpl` is the error message format taking the bad edge as a
                   positional argument.
        `edge` is the bad edge.

        """
        super().__init__(Template(msg_tmpl).substitute({self.EDGE_KEY: edge}))
        self._edge = edge

    @property
    def edge(self) -> object:
        """Bad edge

        `self` is this bad edge error.

        """
        return self._edge

    EDGE_KEY: Final = "edge"  # parameter key in message format


class BadWidthError(RuntimeError):

    """Bad Width error

    A unit width is bad if it isn't positive.

    """

    def __init__(self, msg_tmpl: str, unit: object, width: object) -> None:
        """Create a bad width error.

        `self` is this bad width error.
        `msg_tmpl` is the error message format taking in order the
                   offending unit and width as positional arguments.
        `unit` is the unit with a bad width.
        `width` is the bad width.

        """
        super().__init__(Template(msg_tmpl).substitute(
            {self.UNIT_KEY: unit, self.WIDTH_KEY: width}))
        self._unit = unit
        self._width = width

    @property
    def unit(self) -> object:
        """Unit having the bad width

        `self` is this bad width error.

        """
        return self._unit

    @property
    def width(self) -> object:
        """Bad width

        `self` is this bad width error.

        """
        return self._width

    # parameter keys in message format
    UNIT_KEY: Final = "unit"

    WIDTH_KEY: Final = "width"


@attr.s(auto_attribs=True, frozen=True)
class ComponentInfo:

    """Component information"""

    std_name: ICaseString

    reporting_name: object


@attr.s(auto_attribs=True, frozen=True)
class CapPortInfo:

    """Capability-port combination information"""

    capability_info: ComponentInfo

    port_info: ComponentInfo


class BlockedCapError(RuntimeError):

    """Blocked Input capability error

    A blocked input capability is one that if fed to a supporting input
    port won't reach all outputs with full or partial width from the
    input it was fed to.

    """

    def __init__(self, msg_tmpl: str, blocking_info: CapPortInfo) -> None:
        """Create a blocked input capability error.

        `self` is this blocked input capability error.
        `msg_tmpl` is the error message format taking in order the
                   capability, port, actual, and maximum bus widths as
                   positional arguments.
        `blocking_info` is the blocking information.

        """
        super().__init__(Template(msg_tmpl).substitute(
            {self.CAPABILITY_KEY: blocking_info.capability_info.reporting_name,
             self.PORT_KEY: blocking_info.port_info.reporting_name}))
        self._capability = blocking_info.capability_info.std_name
        self._port = blocking_info.port_info.std_name

    @property
    def capability(self) -> ICaseString:
        """Blocked capability

        `self` is this blocked input capability error.

        """
        return self._capability

    @property
    def port(self) -> ICaseString:
        """Port the capability is block at

        `self` is this blocked input capability error.

        """
        return self._port

    # parameter keys in message format
    CAPABILITY_KEY: Final = "capability"

    PORT_KEY: Final = "port"


class DeadInputError(RuntimeError):

    """Dead input port error

    A dead input port is one that is connected to units none of which is
    supporting any of the input port capabilities.

    """

    def __init__(self, msg_tmpl: str, port: object) -> None:
        """Create a dead input error.

        `self` is this dead input error.
        `msg_tmpl` is the error message format taking the blocked port
                   as a positional argument.
        `port` is the blocked input port.

        """
        super().__init__(Template(msg_tmpl).substitute({self.PORT_KEY: port}))
        self._port = port

    @property
    def port(self) -> object:
        """Blocked input port

        `self` is this dead input error.

        """
        return self._port

    PORT_KEY: Final = "port"  # parameter key in message format


class DupElemError(RuntimeError):

    """Duplicate set element error"""

    def __init__(
            self, msg_tmpl: str, old_elem: object, new_elem: object) -> None:
        """Create a duplicate element error.

        `self` is this duplicate element error.
        `msg_tmpl` is the error message format taking in order the old
                   and new elements as positional arguments.
        `old_elem` is the element already existing.
        `new_elem` is the element just discovered.

        """
        super().__init__(Template(msg_tmpl).substitute(
            {self.OLD_ELEM_KEY: old_elem, self.NEW_ELEM_KEY: new_elem}))
        self._old_elem = old_elem
        self._new_elem = new_elem

    @property
    def new_element(self) -> object:
        """Duplicate element just discovered

        `self` is this duplicate element error.

        """
        return self._new_elem

    @property
    def old_element(self) -> object:
        """Element added before

        `self` is this duplicate element error.

        """
        return self._old_elem

    # parameter keys in message format
    OLD_ELEM_KEY: Final = "old_elem"

    NEW_ELEM_KEY: Final = "new_elem"


class EmptyProcError(RuntimeError):

    """Empty processor error"""


class PathLockError(RuntimeError):

    """Path lock error"""

    def __init__(self, msg_tmpl: str, start: object, lock_type: object,
                 capability: object) -> None:
        """Create a multi-lock error.

        `self` is this multi-lock error.
        `msg_tmpl` is the error message format taking the multi-lock
                   segment as a positional argument.
        `start` is the path start unit.
        `lock_type` is the type of locks along the path.
        `capability` is the capability for which the path was computed.

        """
        super().__init__(Template(msg_tmpl).substitute(
            {self.CAP_KEY: capability, self.LOCK_TYPE_KEY: lock_type,
             self.START_KEY: start}))
        self._start = start
        self._lock_type = lock_type
        self._capability = capability

    @property
    def capability(self) -> object:
        """capability of the path

        `self` is this multi-lock error.

        """
        return self._capability

    @property
    def lock_type(self) -> object:
        """type of locks along the path

        `self` is this multi-lock error.

        """
        return self._lock_type

    @property
    def start(self) -> object:
        """path start point

        `self` is this multi-lock error.

        """
        return self._start

    # parameter keys in message format
    CAP_KEY: Final = "capability"

    LOCK_TYPE_KEY: Final = "lock_type"

    START_KEY: Final = "start"
