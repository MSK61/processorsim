# -*- coding: utf-8 -*-

"""processor sanity checks"""

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
# file:         _checks.py
#
# function:     chk_caps, chk_cycles and chk_non_empty
#
# description:  contains processor structure analysis and checking
#               routines
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

import typing
from typing import (
    AbstractSet,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    Tuple,
)

import attr
import fastcore.foundation
from fastcore.foundation import Self
import iteration_utilities
import more_itertools
import networkx
from networkx import DiGraph, Graph

from str_utils import ICaseString
from . import cap_anal_utils, exception, _port_defs, units
from .exception import BlockedCapError, ComponentInfo, PathLockError
from .units import UNIT_CAPS_KEY, UNIT_WIDTH_KEY

_OLD_NODE_KEY: typing.Final = "old_node"
_T = typing.TypeVar("_T")


def chk_caps(processor: DiGraph) -> None:
    """Perform per-capability checks.

    `processor` is the processor to check whose capabilities.

    """
    cap_checks = [
        lambda cap_graph, post_ord, cap, in_ports, _: _chk_multilock(
            cap_graph, post_ord, cap, in_ports
        )
    ]

    if processor.number_of_nodes() > 1:
        cap_checks.append(
            lambda cap_graph, _, cap, in_ports, out_ports: _chk_cap_flow(
                _get_anal_graph(cap_graph),
                ComponentInfo(cap, "Capability " + cap),
                in_ports,
                out_ports,
                lambda port: "port " + port,
            )
        )

    _do_cap_checks(processor, cap_checks)


def chk_cycles(processor: Graph) -> None:
    """Check the given processor for cycles.

    `processor` is the processor to check.
    The function raises a NetworkXUnfeasible if the processor isn't a
    DAG.

    """
    if not networkx.is_directed_acyclic_graph(processor):
        raise networkx.NetworkXUnfeasible


def chk_non_empty(
    processor: typing.Container[object], in_ports: Iterable[object]
) -> None:
    """Check if the processor still has input ports.

    `processor` is the processor to check.
    `in_ports` are the processor original input ports.
    The function raises an EmptyProcError if no input ports still exist.

    """
    if not more_itertools.first_true(
        in_ports, pred=lambda port: port in processor
    ):
        raise exception.EmptyProcError("No input ports found")


@attr.s(auto_attribs=True, frozen=True)
class _SatInfo:

    """Lock saturation information"""

    read_lock: int

    write_lock: int


@attr.s(auto_attribs=True, frozen=True)
class _PathDescriptor:

    """Path descriptor in multi-lock analysis"""

    @classmethod
    def make_read_desc(
        cls, capability: object, start: object
    ) -> "_PathDescriptor":
        """Create a read lock path description.

        `cls` is the created object class.
        `capability` is the path capability.
        `start` is the path start unit.

        """
        return cls(Self.read_lock(), "read", capability, start)

    @classmethod
    def make_write_desc(
        cls, capability: object, start: object
    ) -> "_PathDescriptor":
        """Create a write lock path description.

        `cls` is the created object class.
        `capability` is the path capability.
        `start` is the path start unit.

        """
        return cls(Self.write_lock(), "write", capability, start)

    selector: typing.Callable[[_SatInfo], int]

    lock_type: object

    capability: object

    start: object


@attr.s(auto_attribs=True, frozen=True)
class _PathLockCalc:

    """Path lock calculator"""

    def calc_lock(
        self,
        lock_key: object,
        path_desc_fact: Callable[[object, object], _PathDescriptor],
    ) -> int:
        """Calculate the path lock.

        `self` is this path lock calculator.
        `lock_key` is the lock key in the unit.
        `path_desc_fact` is the path description factory function.

        """
        return self._calc_path_lock(
            self._start_unit[lock_key],
            path_desc_fact(self._capability, self._start_name),
        )

    def _get_tail_lock(self, path_desc: _PathDescriptor) -> int:
        """Get the common lock of tail paths.

        `self` is this path lock calculator.
        `path_desc` is the path descriptor.
        The method returns the lock of successor paths, which has to be
        the same for all units. If the paths have different locks, the
        method raises a PathLockError. If the given list of units is
        empty, the method returns a negative value.

        """
        one_lock = -1

        for cur_succ in self._succ_lst:
            one_lock = _update_lock(
                one_lock,
                path_desc.selector(self._path_locks[cur_succ]),
                path_desc,
            )

        return one_lock

    def _calc_path_lock(
        self, unit_lock: bool, path_desc: _PathDescriptor
    ) -> int:
        """Calculate the path lock.

        `self` is this path lock calculator.
        `unit_lock` is the lock status of the unit.
        `path_desc` is the path descriptor.
        The method raises a PathLockError if any path originating from
        the start unit has multiple locks or differnt paths have
        different locks.

        """
        path_lock = 1 if unit_lock else 0
        tail_lock = self._get_tail_lock(path_desc)

        if tail_lock >= 0:
            path_lock += tail_lock

        _chk_seg_lock(path_lock, path_desc)
        return path_lock

    _start_unit: Mapping[object, bool]

    _succ_lst: typing.Collection[object]

    _capability: object

    _start_name: object

    _path_locks: Mapping[object, _SatInfo]


def _add_port_link(graph: Graph, old_port: object, new_port: object) -> None:
    """Add a link between old and new ports.

    `graph` is the graph containing ports.
    `old_port` is the old port.
    `new_port` is the new port.

    """
    graph.nodes[new_port][UNIT_WIDTH_KEY] += graph.nodes[old_port][
        UNIT_WIDTH_KEY
    ]
    graph.add_edge(old_port, new_port)


def _aug_out_ports(processor: Graph, out_ports: Sequence[object]) -> object:
    """Unify the output ports in the processor.

    `processor` is the processor containing the output ports.
    `out_ports` are the output ports to weld.
    The function connects several output ports into a single output port
    and returns that single port.

    """
    return _aug_terminals(processor, out_ports)


def _aug_terminals(graph: Graph, ports: Sequence[object]) -> object:
    """Unify terminals indicated by degrees in the graph.

    `graph` is the graph containing terminals.
    `ports` are the terminals to unify.
    The function tries to connect several terminals into a single new
    terminal. The function returns the newly added port.

    """
    return ports[0] if len(ports) == 1 else _unify_ports(graph, ports)


def _cap_in_edge(
    processor: Graph, capability: object, edge: Iterable[object]
) -> bool:
    """Check if the given capability is supported by the edge.

    `processor` is the processor containing the edge.
    `capability` is the capability to check.
    `edge` is the edge to check.

    """
    return all(_cap_in_unit(processor, capability, unit) for unit in edge)


def _cap_in_unit(processor: Graph, capability: object, unit: object) -> bool:
    """Check if the given capability is supported by the unit.

    `processor` is the processor containing the unit.
    `capability` is the capability to check.
    `unit` is the unit to check.

    """
    return capability in processor.nodes[unit][UNIT_CAPS_KEY]


def _chk_cap_flow(
    anal_graph: DiGraph,
    capability_info: ComponentInfo,
    in_ports: Iterable[ICaseString],
    out_ports: Iterable[object],
    port_name_func: Callable[[ICaseString], object],
) -> None:
    """Check the flow capacity for the given capability and ports.

    `anal_graph` is the analysis graph.
    `capability_info` is the capability information.
    `in_ports` are the input ports supporting the given capability.
    `out_ports` are the output ports of the original processor.
    `port_name_func` is the port reporting name function.
    The function raises a BlockedCapError if the capability through any
    input port can't flow with full or partial capacity from this input
    port to the output ports.

    """
    node_items = anal_graph.nodes.items()
    unit_anal_map = {
        unit_attrs[_OLD_NODE_KEY]: unit for unit, unit_attrs in node_items
    }
    unified_out = _aug_out_ports(
        anal_graph, [unit_anal_map[port] for port in out_ports]
    )
    unified_out = cap_anal_utils.split_nodes(anal_graph)[unified_out]
    _dist_edge_caps(anal_graph)

    for cur_port in in_ports:
        _chk_unit_flow(
            networkx.maximum_flow_value(
                anal_graph, unit_anal_map[cur_port], unified_out
            ),
            capability_info,
            ComponentInfo(cur_port, port_name_func(cur_port)),
        )


def _chk_in_lock(in_lock_info: _SatInfo, path_desc: _PathDescriptor) -> None:
    """Check if paths from the input port don't have exactly one lock.

    `in_lock_info` is the input lock information.
    `path_desc` is the path descriptor.
    The function raises a PathLockError if any paths with multiple locks
    exist at the given port.

    """
    if not path_desc.selector(in_lock_info):
        raise PathLockError(
            f"Found a path starting at input port ${PathLockError.START_KEY} "
            f"with no ${PathLockError.LOCK_TYPE_KEY} locks for capability "
            f"${PathLockError.CAP_KEY}.",
            path_desc.start,
            path_desc.lock_type,
            path_desc.capability,
        )


def _chk_in_locks(
    in_ports: Iterable[object],
    path_locks: Mapping[object, _SatInfo],
    capability: object,
) -> None:
    """Check if paths from input ports don't have exactly one lock.

    `in_ports` are the input ports to check whose locks.
    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    `capability` is the capability for which input paths are inspected.
    The function raises a PathLockError if any paths with multiple locks
    exist at any port.

    """
    for cur_port in in_ports:
        for path_desc_fact in [
            _PathDescriptor.make_read_desc,
            _PathDescriptor.make_write_desc,
        ]:
            _chk_in_lock(
                path_locks[cur_port], path_desc_fact(capability, cur_port)
            )


def _chk_multilock(
    processor: DiGraph,
    post_ord: Iterable[object],
    capability: object,
    in_ports: Iterable[object],
) -> None:
    """Check if the processor has paths with multiple locks.

    `processor` is the processor to check for multi-lock paths.
    `post_ord` is the post-order of the processor functional units.
    `capability` is the capability of lock paths under consideration.
    `in_ports` are the input ports supporting the given capability.
    The function raises a PathLockError if any paths with multiple locks
    exist.

    """
    path_locks: Dict[object, _SatInfo] = {}

    for unit in post_ord:
        _chk_path_locks(unit, processor, path_locks, capability)

    _chk_in_locks(in_ports, path_locks, capability)


def _chk_path_locks(
    start: object,
    processor: DiGraph,
    path_locks: MutableMapping[object, _SatInfo],
    capability: object,
) -> None:
    """Check if paths from the given start unit contains multiple locks.

    `start` is the starting unit of paths to check.
    `processor` is the processor containing the start unit.
    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    `capability` is the capability of lock paths under consideration.
    The function raises a PathLockError if any paths originating from
    the given unit have multiple locks.

    """
    succ_lst = tuple(processor.successors(start))
    # because pylint can't detect packed as a member of
    # iteration_utilities
    # pylint: disable=no-member
    sat_params = map(
        iteration_utilities.packed(
            _PathLockCalc(
                processor.nodes[start], succ_lst, capability, start, path_locks
            ).calc_lock
        ),
        [
            (units.UNIT_RLOCK_KEY, _PathDescriptor.make_read_desc),
            (units.UNIT_WLOCK_KEY, _PathDescriptor.make_write_desc),
        ],
    )
    # pylint: disable=no-member
    path_locks[start] = _SatInfo(*sat_params)


def _chk_seg_lock(seg_lock: int, seg_desc: _PathDescriptor) -> None:
    """Check if the segment has exceeded the maximum allowed lock.

    `seg_desc` is the segment descriptor.
    `seg_lock` is the segment lock.
    The method raises a PathLockError if the segment has multiple locks.

    """
    if seg_lock > 1:
        raise PathLockError(
            f"Found a path passing through ${PathLockError.START_KEY} with "
            f"multiple ${PathLockError.LOCK_TYPE_KEY} locks for capability "
            f"${PathLockError.CAP_KEY}.",
            seg_desc.start,
            seg_desc.lock_type,
            seg_desc.capability,
        )


def _chk_unit_flow(
    min_width: bool, capability_info: ComponentInfo, port_info: ComponentInfo
) -> None:
    """Check the flow volume from an input port to outputs.

    `min_width` is the minimum bus width.
    `capability_info` is the information of the capability whose flow is
                      checked.
    `port_info` is the information of the port the flow is checked
                starting from.
    The function raises a BlockedCapError if the minimum bus width is
    zero.

    """
    if not min_width:
        raise BlockedCapError(
            f"${BlockedCapError.CAPABILITY_KEY} blocked from "
            f"${BlockedCapError.PORT_KEY}",
            exception.CapPortInfo(capability_info, port_info),
        )


def _coll_cap_edges(graph: DiGraph) -> typing.FrozenSet[_T]:
    """Collect capping edges from the given graph.

    `graph` is the graph to collect edges from.
    The function returns capping edges. A capping edge is the sole edge
    on either side of a node that determines the maximum flow through
    the node.

    """
    in_degrees = iteration_utilities.starfilter(
        lambda node, in_deg: in_deg == 1 or graph.out_degree(node) == 1,
        graph.in_degree,
    )
    return frozenset(
        _get_cap_edge(graph.in_edges(node), graph.out_edges(node))
        for node, _ in in_degrees
    )


def _dist_edge_caps(graph: DiGraph) -> None:
    """Distribute capacities over edges as needed.

    `graph` is the graph containing edges.
    The function distributes capacities over capping edges.

    """
    _set_capacities(graph, _coll_cap_edges(graph))


def _do_cap_checks(
    processor: DiGraph,
    cap_checks: Iterable[
        Callable[
            [
                DiGraph,
                Iterable[object],
                ICaseString,
                Iterable[ICaseString],
                Iterable[object],
            ],
            None,
        ]
    ],
) -> None:
    """Perform per-capability checks.

    `processor` is the processor to check.
    `cap_checks` are the checks to perform.

    """
    cap_units: AbstractSet[
        Tuple[ICaseString, List[ICaseString]]
    ] = _get_cap_units(processor)
    out_ports = tuple(_port_defs.get_out_ports(processor))
    post_ord = tuple(networkx.dfs_postorder_nodes(processor))

    for cap, in_ports in cap_units:
        for cur_chk in cap_checks:
            cur_chk(
                _make_cap_graph(processor, cap),
                _filter_by_cap(post_ord, cap, processor),
                cap,
                in_ports,
                out_ports,
            )


def _filter_by_cap(
    post_ord: Iterable[object], capability: object, processor: Graph
) -> Generator[object, None, None]:
    """Filter the given units by the specified capability.

    `post_ord` is the post-order of the processor functional units.
    `capability` is the capability to filter units by.
    `processor` is the processor containing the units.
    The function returns an iterable over only the units having the
    given capability.

    """
    return (
        unit for unit in post_ord if _cap_in_unit(processor, capability, unit)
    )


def _get_anal_graph(processor: Graph) -> DiGraph:
    """Create a processor bus width analysis graph.

    `processor` is the processor to build an analysis graph from.

    """
    width_graph = DiGraph()
    hw_units = enumerate(processor)
    new_nodes: Dict[object, object] = {}

    for idx, unit in hw_units:
        _update_graph(idx, unit, processor, width_graph, new_nodes)

    width_graph.add_edges_from(
        fastcore.foundation.map_ex(edge, new_nodes) for edge in processor.edges
    )
    return width_graph


def _get_cap_edge(in_edges: Iterable[_T], out_edges: Iterable[_T]) -> _T:
    """Select the capping edge.

    `in_edges` are an iterator over input edges.
    `out_edges` are an iterator over output edges.
    A capping edge is the sole edge on either side of a node that
    determines the maximum flow through the node. Either the input edges
    or the output edges must contain exactly one edge.

    """
    try:
        return more_itertools.one(in_edges)
    except ValueError:
        return more_itertools.first(out_edges)


def _get_cap_units(
    processor: DiGraph,
) -> AbstractSet[Tuple[ICaseString, List[_T]]]:
    """Create a mapping between capabilities and supporting input ports.

    `processor` is the processor to create a capability-port map for.
    The function returns an iterable of tuples; each tuple represents a
    capability and its supporting units.

    """
    cap_unit_map: Dict[ICaseString, List[_T]] = {}
    in_ports: Generator[_T, None, None] = _port_defs.get_in_ports(processor)

    for cur_port in in_ports:
        for cur_cap in processor.nodes[cur_port][UNIT_CAPS_KEY]:
            cap_unit_map.setdefault(cur_cap, []).append(cur_port)

    return cap_unit_map.items()


def _make_cap_graph(processor: Graph, capability: object) -> DiGraph:
    """Create a graph condensed for the given capability.

    `processor` is the processor to create a graph from.
    `capability` is the capability to consider while constructing the
                 graph.
    The function creates a graph with all units in the original
    processor but only with edges connecting units having the given
    capability in common.

    """
    cap_graph = DiGraph(
        edge
        for edge in processor.edges
        if _cap_in_edge(processor, capability, edge)
    )
    cap_graph.add_nodes_from(processor.nodes.items())
    return cap_graph


def _set_capacities(
    graph: Graph, cap_edges: Iterable[Tuple[object, object]]
) -> None:
    """Assign capacities to capping edges.

    `graph` is the graph containing edges.
    `cap_edges` are the capping edges.

    """
    for cur_edge in cap_edges:
        graph[cur_edge[0]][cur_edge[1]]["capacity"] = min(
            graph.nodes[unit][UNIT_WIDTH_KEY] for unit in cur_edge
        )


def _unify_ports(graph: Graph, ports: Iterable[object]) -> int:
    """Unify ports in the graph.

    `graph` is the graph containing terminals.
    `ports` are the ports to unify.
    The function returns the new port.

    """
    unified_port = graph.number_of_nodes()
    graph.add_node(unified_port, **{UNIT_WIDTH_KEY: 0})

    for cur_port in ports:
        _add_port_link(graph, cur_port, unified_port)

    return unified_port


def _update_graph(
    idx: object,
    unit: object,
    processor: Graph,
    width_graph: Graph,
    unit_idx_map: MutableMapping[object, object],
) -> None:
    """Update width graph structures.

    `idx` is the unit index.
    `unit` is the unit name.
    `processor` is the original processor.
    `width_graph` is the bus width analysis graph.
    `unit_idx_map` is the mapping between unit names and indices.

    """
    width_graph.add_node(idx, **processor.nodes[unit], **{_OLD_NODE_KEY: unit})
    unit_idx_map[unit] = idx


def _update_lock(
    old_lock: int, new_lock: int, path_desc: _PathDescriptor
) -> int:
    """Update the lock based on the current and proposed values.

    `old_lock` is the lock value so far.
    `new_lock` is the new proposed lock value.
    `path_desc` is the descriptor of the path for which the lock is
                updated.
    The method initializes the current lock value if it hasn't already
    been initialized, otherwise it makes sure the new value matches the
    old one. If the new value is different from the current one, the
    method raises a PathLockError. The method returns the updated lock.

    """
    if old_lock < 0 or new_lock == old_lock:
        return new_lock

    raise PathLockError(
        f"Paths passing through ${PathLockError.START_KEY} have different "
        f"${PathLockError.LOCK_TYPE_KEY} locks for capability "
        f"${PathLockError.CAP_KEY}.",
        path_desc.start,
        path_desc.lock_type,
        path_desc.capability,
    )
