# -*- coding: utf-8 -*-

"""capability analysis utilities"""

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
# file:         cap_anal_utils.py
#
# function:     capability analysis utilities
#
# description:  contains capability analysis services
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
import typing

from networkx import DiGraph, Graph

from .units import UNIT_WIDTH_KEY


def split_nodes(graph: DiGraph) -> typing.Dict[object, object]:
    """Split nodes in the given graph as necessary.

    `graph` is the graph containing nodes.
    The function splits nodes having multiple links on one side and a
    non-capping link on the other. A link on one side is capping if it's
    the only link on this side.
    The function returns a dictionary mapping each unit to its output
    twin(if one was created) or itself if it wasn't split.

    """
    in_degrees = tuple(graph.in_degree)
    return {
        unit: _split_node(graph, unit, len(in_degrees) + unit)
        if twin != 1
        and graph.out_degree[unit] != 1
        and (twin or graph.out_degree[unit])
        else unit
        for unit, twin in in_degrees
    }


def _mov_out_link(
    graph: Graph, link: tuple[object, object], new_node: object
) -> None:
    """Move an outgoing link from an old node to a new one.

    `graph` is the graph containing the nodes.
    `link` is the outgoing link to move.
    `new_node` is the node to move the outgoing link to.

    """
    graph.add_edge(new_node, link[1])
    graph.remove_edge(*link)


def _mov_out_links(
    graph: Graph,
    out_links: collections.abc.Iterable[tuple[object, object]],
    new_node: object,
) -> None:
    """Move outgoing links from an old node to a new one.

    `graph` is the graph containing the nodes.
    `out_links` are the outgoing links to move.
    `new_node` is the node to move the outgoing links to.

    """
    for cur_link in out_links:
        _mov_out_link(graph, cur_link, new_node)


def _split_node(graph: DiGraph, old_node: object, new_node: object) -> object:
    """Split a node into old and new ones.

    `graph` is the graph containing the node to be split.
    `old_node` is the existing node.
    `new_node` is the node added after splitting.
    The function returns the new node.

    """
    graph.add_node(
        new_node, **{UNIT_WIDTH_KEY: graph.nodes[old_node][UNIT_WIDTH_KEY]}
    )
    _mov_out_links(graph, tuple(graph.out_edges(old_node)), new_node)
    graph.add_edge(old_node, new_node)
    return new_node
