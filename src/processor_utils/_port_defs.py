# -*- coding: utf-8 -*-

"""port definitions"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
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
# file:         _port_defs.py
#
# function:     get_in_ports and get_out_ports
#
# description:  port definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
from collections.abc import Generator
import typing

from fastcore import foundation
from networkx import DiGraph

_T = typing.TypeVar("_T")


def get_in_ports(processor: DiGraph) -> Generator[_T, None, None]:
    """Find the input ports.

    `processor` is the processor to find whose input ports.
    The function returns an iterator over the processor input ports.

    """
    return _get_ports(processor.in_degree)


def get_out_ports(processor: DiGraph) -> Generator[object, None, None]:
    """Find the output ports.

    `processor` is the processor to find whose output ports.
    The function returns an iterator over the processor output ports.

    """
    return _get_ports(processor.out_degree)


class PortGroup:

    """Port group information"""

    def __init__(self, processor: DiGraph) -> None:
        """Extract port information from the given processor.

        `self` is this port group.
        `processor` is the processor to extract port group information
                    from.

        """
        self._in_ports, self._out_ports = foundation.maps(
            foundation.Self(processor), tuple, [get_in_ports, get_out_ports]
        )

    @property
    def in_ports(self) -> tuple[object, ...]:
        """Input ports

        `self` is this port group.

        """
        return self._in_ports

    @property
    def out_ports(self) -> tuple[object, ...]:
        """Output ports

        `self` is this port group.

        """
        return self._out_ports


def _get_ports(
    degrees: collections.abc.Iterable[tuple[_T, bool]]
) -> Generator[_T, None, None]:
    """Find the ports with respect to the given degrees.

    `degrees` are the degrees of all units.
    A port is a unit with zero degree.

    """
    return (unit for unit, deg in degrees if not deg)
