# -*- coding: utf-8 -*-

"""processor loading exceptions"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.89.0, python 3.11.9, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

from typing import Final

from attr import field, frozen
from fastcore import foundation
from fastcore.foundation import mapt
from pydash import spread

from errors import ElementValue, ErrorElement, EXCEPTION, SimErrorBase


@EXCEPTION
class BadEdgeError(SimErrorBase):
    """Bad edge error"""

    def __init__(self, msg_tmpl: str, edge: object) -> None:
        """Create a bad edge error.

        `self` is this bad edge error.
        `msg_tmpl` is the error message format taking the bad edge as a
                   keyword argument.
        `edge` is the bad edge.

        """
        self._init_simple(msg_tmpl, [ErrorElement(self.EDGE_KEY, edge)])

    edge: object = field()

    EDGE_KEY: Final = "edge"  # parameter key in message format


@EXCEPTION
class BadWidthError(SimErrorBase):
    """Bad Width error

    A unit width is bad if it isn't positive.

    """

    def __init__(self, msg_tmpl: str, unit: object, width: object) -> None:
        """Create a bad width error.

        `self` is this bad width error.
        `msg_tmpl` is the error message format taking in order the
                   offending unit and width as keyword arguments.
        `unit` is the unit with a bad width.
        `width` is the bad width.

        """
        self._init_simple(
            msg_tmpl,
            mapt(
                spread(ErrorElement),
                [[self.UNIT_KEY, unit], [self.WIDTH_KEY, width]],
            ),
        )

    # error parameters
    unit: object = field()

    width: object = field()

    # parameter keys in message format
    UNIT_KEY: Final = "unit"

    WIDTH_KEY: Final = "width"


@EXCEPTION
class DeadInputError(SimErrorBase):
    """Dead input port error

    A dead input port is one that is connected to units none of which is
    supporting any of the input port capabilities.

    """

    def __init__(self, msg_tmpl: str, port: object) -> None:
        """Create a dead input error.

        `self` is this dead input error.
        `msg_tmpl` is the error message format taking the blocked port
                   as a keyword argument.
        `port` is the blocked input port.

        """
        self._init_simple(msg_tmpl, [ErrorElement(self.PORT_KEY, port)])

    port: object = field()

    PORT_KEY: Final = "port"  # parameter key in message format


@EXCEPTION
class DupElemError(SimErrorBase):
    """Duplicate set element error"""

    def __init__(
        self, msg_tmpl: str, old_elem: object, new_elem: object
    ) -> None:
        """Create a duplicate element error.

        `self` is this duplicate element error.
        `msg_tmpl` is the error message format taking in order the old
                   and new elements as keyword arguments.
        `old_elem` is the element already existing.
        `new_elem` is the element just discovered.

        """
        self._init_simple(
            msg_tmpl,
            mapt(
                spread(ErrorElement),
                [[self.OLD_ELEM_KEY, old_elem], [self.NEW_ELEM_KEY, new_elem]],
            ),
        )

    # parameter keys in message format
    OLD_ELEM_KEY: Final = "old_elem"

    NEW_ELEM_KEY: Final = "new_elem"

    # error parameters
    old_element: object = field()

    new_element: object = field()


class EmptyProcError(RuntimeError):
    """Empty processor error"""


@EXCEPTION
class PathLockError(SimErrorBase):
    """Path lock error"""

    def __init__(
        self,
        msg_tmpl: str,
        start: object,
        lock_type: object,
        capability: object,
    ) -> None:
        """Create a multi-lock error.

        `self` is this multi-lock error.
        `msg_tmpl` is the error message format taking the multi-lock
                   segment as a keyword argument.
        `start` is the path start unit.
        `lock_type` is the type of locks along the path.
        `capability` is the capability for which the path was computed.

        """
        self._init_simple(
            msg_tmpl,
            mapt(
                spread(ErrorElement),
                [
                    [self.CAP_KEY, capability],
                    [self.LOCK_TYPE_KEY, lock_type],
                    [self.START_KEY, start],
                ],
            ),
        )

    # parameter keys in message format
    CAP_KEY: Final = "capability"

    LOCK_TYPE_KEY: Final = "lock_type"

    START_KEY: Final = "start"

    # error parameters
    capability: object = field()

    lock_type: object = field()

    start: object = field()


@frozen
class ComponentInfo:
    """Component information"""

    std_name: str

    reporting_name: object


@frozen
class CapPortInfo:
    """Capability-port combination information"""

    capability_info: ComponentInfo

    port_info: ComponentInfo


@EXCEPTION
class BlockedCapError(SimErrorBase):
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
                   keyword arguments.
        `blocking_info` is the blocking information.

        """
        self._init(
            msg_tmpl,
            [
                ErrorElement(key, self._make_elem_val(comp))
                for key, comp in [
                    (self.CAPABILITY_KEY, blocking_info.capability_info),
                    (self.PORT_KEY, blocking_info.port_info),
                ]
            ],
        )

    @staticmethod
    def _make_elem_val(comp: ComponentInfo) -> ElementValue:
        """Create an element value out of a component.

        `comp` is the component to use for creating the element value.

        """
        return ElementValue(
            *(
                attr_getter(comp)
                for attr_getter in [
                    foundation.Self.reporting_name(),
                    foundation.Self.std_name(),
                ]
            )
        )

    # error parameters
    capability: str = field()

    port: str = field()

    # parameter keys in message format
    CAPABILITY_KEY: Final = "capability"

    PORT_KEY: Final = "port"
