# -*- coding: utf-8 -*-

"""wrappers for appeasing type checkers"""

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
# file:         type_checking.py
#
# function:     type checking clutches
#
# description:  contains wrappers for services that might upset type
#               checkers
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.91.1, python 3.11.9, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
from typing import Any, cast, TypeVar

import fastcore.foundation
import networkx
from networkx.classes import reportviews

_AnyT = TypeVar("_AnyT", bound=Any)
_T = TypeVar("_T")


def map_ex(seq: Any, map_func: Any, _: type[_T]) -> "map[_T]":
    """Map an iterable using a mapping function.

    `seq` is the iterable to map.
    `map_func` is the mapping function.
    `_` is the type of elements in the resulting mapped generator.
    I'm casting to map[_T] due to a missing explicit type hint for the
    return type of the fastcore.foundation.map_ex function.

    """
    return cast("map[_T]", fastcore.foundation.map_ex(seq, map_func, gen=True))


def nodes(
    graph: networkx.Graph, data: Any
) -> reportviews.NodeDataView | reportviews.NodeView:
    """Retrieve the node data view of the given graph.

    `graph` is the graph to retrieve whose node data view.
    `data` is the data to fill in the node data view.
    I'm casting data to bool due to a missing explicit type hint for the
    Graph.nodes function. The type inferred by pylance for the first
    parameter to networkx.Graph.nodes is(wrongfully) bool(because that's
    what the default value for that parameter implies).

    """
    return graph.nodes(cast(bool, data))  # type: ignore[reportArgumentType]


def sorted_lst(seq: collections.abc.Iterable[_AnyT]) -> list[_AnyT]:
    """Create a sorted list of the given iterable.

    `seq` is the iterable to sort.
    As I don't want to rely on unstable API from typeshed, I'm just
    relaxing the checks against the item type of the given iterable.

    """
    return sorted(seq)
