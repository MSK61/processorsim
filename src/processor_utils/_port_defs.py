# -*- coding: utf-8 -*-

"""port definitions"""

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
# file:         _port_defs.py
#
# function:     get_in_ports and get_out_ports
#
# description:  port definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.95.1, python 3.12.7, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
from collections.abc import Generator, Iterable
import typing
from typing import Any

import attr
import fastcore.basics
from networkx import DiGraph

import type_checking

_T = typing.TypeVar("_T")


def get_in_ports(processor: DiGraph) -> Generator[Any, None, None]:
    """Find the input ports.

    `processor` is the processor to find whose input ports.
    The function returns an iterator over the processor input ports.

    """
    return _get_ports(processor.in_degree)


def get_out_ports(processor: DiGraph) -> Generator[Any, None, None]:
    """Find the output ports.

    `processor` is the processor to find whose output ports.
    The function returns an iterator over the processor output ports.

    """
    return _get_ports(processor.out_degree)


@attr.frozen
class PortGroup:
    """Port group information"""

    def __init__(self, proc_supplier: object) -> None:
        """Extract port information from the indicated processor.

        `self` is this port group.
        `proc_supplier` is a functor that takes a function and calls it
                        with a pre-configured processor.

        """
        type_checking.attrs_init(
            self,
            *(
                fastcore.basics.maps(
                    proc_supplier, tuple, [get_in_ports, get_out_ports]
                )
            )
        )

    in_ports: collections.abc.Collection[object]

    out_ports: Iterable[object]


def _get_ports(degrees: Iterable[Iterable[_T]]) -> Generator[_T, None, None]:
    """Find the ports with respect to the given degrees.

    `degrees` are the degrees of all units.
    A port is a unit with zero degree.

    """
    return (unit for unit, deg in degrees if not deg)
