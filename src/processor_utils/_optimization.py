# -*- coding: utf-8 -*-

"""processor optimization procedures"""

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
# file:         _optimization.py
#
# function:     chk_terminals, clean_struct and rm_empty_units
#
# description:  contains processor optimization operations
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.74.1, python 3.10.8, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################

from logging import warning
import typing
from typing import FrozenSet

import networkx
from networkx import DiGraph, Graph

from str_utils import ICaseString
from .exception import DeadInputError
from .units import UNIT_CAPS_KEY
from . import _port_defs


def chk_terminals(
    processor: DiGraph, orig_port_info: _port_defs.PortGroup
) -> None:
    """Check if new terminals have appeared after optimization.

    `processor` is the processor to check.
    `orig_port_info` is the original port information(before
                     optimization).
    The function removes spurious output ports that might have appeared
    after trimming actions during optimization.

    """
    new_out_ports = frozenset(_port_defs.get_out_ports(processor)).difference(
        orig_port_info.out_ports
    )

    for out_port in new_out_ports:
        _rm_dead_end(processor, out_port, orig_port_info.in_ports)


def clean_struct(processor: DiGraph) -> None:
    """Clean the given processor structure.

    `processor` is the processor to clean whose structure.
    The function removes capabilities in each unit that aren't supported
    in any of its predecessor units. It also removes incompatible edges(those
    connecting units having no capabilities in common).

    """
    hw_units = networkx.topological_sort(processor)

    for unit in hw_units:
        if processor.in_degree(unit):  # Skip in-ports.
            _clean_unit(processor, unit)


def rm_empty_units(processor: Graph) -> None:
    """Remove empty units from the given processor.

    `processor` is the processor to clean.
    The function removes units with no capabilities from the processor.

    """
    unit_entries = tuple(processor.nodes(UNIT_CAPS_KEY))

    for unit, capabilities in unit_entries:
        if not capabilities:
            _rm_empty_unit(processor, unit)


def _chk_edge(
    processor: Graph, edge: typing.Tuple[object, object]
) -> FrozenSet[ICaseString]:
    """Check if the edge is useful.

    `processor` is the processor containing the edge.
    `edge` is the edge to check.
    The function removes the given edge if it isn't needed. It returns
    the common capabilities between the units connected by the edge.

    """
    common_caps = processor.nodes[edge[1]][UNIT_CAPS_KEY].intersection(
        processor.nodes[edge[0]][UNIT_CAPS_KEY]
    )

    if not common_caps:
        _rm_dummy_edge(processor, edge)

    return common_caps


def _clean_unit(processor: Graph, unit: object) -> None:
    """Clean the given unit properties.

    `processor` is the processor containing the unit.
    `unit` is the unit to clean whose properties.
    The function restricts the capabilities of the given unit to only
    those supported by its predecessors. It also removes incoming edges
    coming from a predecessor unit having no capabilities in common with
    the given unit.

    """
    processor.nodes[unit][UNIT_CAPS_KEY] = frozenset(
        processor.nodes[unit][UNIT_CAPS_KEY]
    )
    pred_caps = (
        _chk_edge(processor, edge) for edge in tuple(processor.in_edges(unit))
    )
    processor.nodes[unit][UNIT_CAPS_KEY] = typing.cast(
        FrozenSet[ICaseString], frozenset()
    ).union(*pred_caps)


def _rm_dead_end(
    processor: Graph, dead_end: object, in_ports: typing.Container[object]
) -> None:
    """Remove a dead end from the given processor.

    `processor` is the processor to remove the dead end from.
    `dead_end` is the dead end to remove.
    `in_ports` are the processor original input ports.
    A dead end is a port that looks like an output port after
    optimization actions have cut it off real output ports.

    """
    if dead_end in in_ports:  # an in-port turned in-out port
        raise DeadInputError(
            "No feasible path found from input port "
            f"${DeadInputError.PORT_KEY} to any output ports",
            dead_end,
        )

    warning("Dead end detected at unit %s, removing...", dead_end)
    processor.remove_node(dead_end)


def _rm_dummy_edge(processor: Graph, edge: typing.Collection[object]) -> None:
    """Remove an edge from the given processor.

    `processor` is the processor to remove the edge from.
    `edge` is the edge to remove.

    """
    warning(
        "Units %s and %s have no capabilities in common, removing connecting "
        "edge...",
        *edge,
    )
    processor.remove_edge(*edge)


def _rm_empty_unit(processor: Graph, unit: object) -> None:
    """Remove a unit from the given processor.

    `processor` is the processor to remove the unit from.
    `unit` is the unit to remove.

    """
    warning("No capabilities defined for unit %s, removing...", unit)
    processor.remove_node(unit)
