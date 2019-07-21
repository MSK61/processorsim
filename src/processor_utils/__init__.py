# -*- coding: utf-8 -*-

"""processor_utils package"""

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
# file:         __init__.py
#
# function:     processor_utils package
#
# description:  processor_utils package export file
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

from container_utils import concat_dicts
from dataclasses import dataclass
from errors import UndefElemError
from . import exception
from .exception import BadEdgeError, BadWidthError, BlockedCapError, \
    ComponentInfo, DeadInputError, DupElemError, MultiLockError
import functools
import itertools
import logging
import networkx
from networkx import dfs_postorder_nodes, DiGraph
from operator import itemgetter
import os
from .sets import IndexedSet, SelfIndexSet
from str_utils import ICaseString
import sys
import typing
from typing import NamedTuple, Tuple
from . import units
from .units import FuncUnit, UnitModel
__all__ = ["exception", "load_proc_desc", "ProcessorDesc", "units"]
_OLD_NODE_KEY = "old_node"
# unit attributes
_UNIT_CAPS_KEY = "capabilities"
_UNIT_NAME_KEY = "name"
# unit lock attributes
_UNIT_RLOCK_KEY = "readLock"
_UNIT_WLOCK_KEY = "writeLock"
_UNIT_WIDTH_KEY = "width"


@dataclass
class ProcessorDesc:

    """Processor description"""

    def __init__(self, in_ports, out_ports, in_out_ports, internal_units):
        """Create a processor.

        `self` is this processor.
        `in_ports` are the input-only ports.
        `out_ports` are the output-only ports.
        `in_out_ports` are the ports that act as both inputs and
                       outputs.
        `internal_units` are the internal units that are neither exposed
                         as inputs nor outputs. Internal units should be
                         specified in post-order with respect to their
                         connecting edges(directed from the producing
                         unit to the consuming one).

        """
        self.in_ports, self.in_out_ports = map(
            units.sorted_models, [in_ports, in_out_ports])
        self.out_ports = self._sorted_units(out_ports)
        self.internal_units = internal_units

    @staticmethod
    def _sorted_units(hw_units):
        """Create a sorted list of the given units.

        `hw_units` are the units to create a sorted list of.

        """
        return tuple(sorted(hw_units, key=lambda unit: unit.model.name))

    in_ports: Tuple[UnitModel]

    out_ports: Tuple[FuncUnit]

    in_out_ports: Tuple[UnitModel]

    internal_units: typing.List[FuncUnit]


class _CapabilityInfo(NamedTuple):

    """Unit capability information"""

    name: ICaseString

    unit: str


@dataclass
class _PathLockInfo:

    """Path locking information"""

    num_of_locks: int

    next_node: ICaseString


class _PortGroup:

    """Port group information"""

    def __init__(self, processor):
        """Extract port information from the given processor.

        `self` is this port group.
        `processor` is the processor to extract port group information
                    from.

        """
        self._in_ports, self._out_ports = map(lambda port_getter: tuple(
            port_getter(processor)), [_get_in_ports, _get_out_ports])

    @property
    def in_ports(self):
        """Input ports

        `self` is this port group.

        """
        return self._in_ports

    @property
    def out_ports(self):
        """Output ports

        `self` is this port group.

        """
        return self._out_ports


class _SatInfo(NamedTuple):

    """Lock saturation information"""

    read_path: _PathLockInfo

    write_path: _PathLockInfo


class _PathDescriptor(NamedTuple):

    """Path descriptor in multi-lock analysis"""

    selector: typing.Callable[[_SatInfo], _PathLockInfo]

    lock_type: str


def get_abilities(processor):
    """Retrieve all capabilities supported by the given processor.

    `processor` is the processor to retrieve whose capabilities.

    """
    return functools.reduce(
        lambda old_caps, port: old_caps.union(port.capabilities),
        processor.in_out_ports + processor.in_ports, frozenset())


def load_isa(raw_desc, capabilities):
    """Transform the given raw description into an instruction set.

    `raw_desc` is the raw description to extract an instruction set
               from.
    `capabilities` are the supported unique capabilities.
    The function returns a mapping between upper-case supported
    instructions and their capabilities.

    """
    return _create_isa(raw_desc, _init_cap_reg(capabilities))


def load_proc_desc(raw_desc):
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    proc_desc = _create_graph(raw_desc["units"], raw_desc["dataPath"])
    _prep_proc_desc(proc_desc)
    return _make_processor(proc_desc)


def _accum_locks(path_locks, path_desc, unit):
    """Accumulate successor locks into the given unit.

    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    `path_desc` is the path descriptor.
    `unit` is the unit to accumulate the successor path to.
    The function accumulates the locks in the successor unit to the path
    starting at the given unit. It raises a MultiLockError if any paths
    originating from the given unit have multiple locks.

    """
    cur_node = path_desc.selector(path_locks[unit])
    cur_node.num_of_locks += path_desc.selector(
        path_locks[cur_node.next_node]).num_of_locks

    if cur_node.num_of_locks > 1:
        raise MultiLockError(
            f"Path segment with multiple ${MultiLockError.LOCK_TYPE_KEY} locks"
            f" found, ${MultiLockError.SEG_KEY}", _create_path(
                path_locks, path_desc.selector, unit), path_desc.lock_type)


def _add_capability(unit, cap, cap_list, unit_cap_reg, global_cap_reg):
    """Add a capability to the given unit.

    `unit` is the unit to add the capability to.
    `cap` is the capability to add.
    `cap_list` is the list of capabilities in the given unit.
    `unit_cap_reg` is the store of previously added capabilities in the
                   given unit.
    `global_cap_reg` is the store of added capabilities across all units
                     so far.

    """
    old_cap = unit_cap_reg.get(cap)

    if old_cap is None:
        _add_new_cap(
            _CapabilityInfo(cap, unit), cap_list, unit_cap_reg, global_cap_reg)
    else:
        logging.warning(
            "Capability %s previously added as %s for unit %s, ignoring...",
            cap, old_cap, unit)


def _add_edge(processor, edge, unit_registry, edge_registry):
    """Add an edge to a processor.

    `processor` is the processor to add the edge to.
    `edge` is the edge to add.
    `unit_registry` is the store of defined units.
    `edge_registry` is the store of previously added edges.
    The function raises a BadEdgeError if the edge doesn't connect
    exactly two units and an UndefElemError if an undefined unit is
    encountered.

    """
    good_edge_len = 2

    if len(edge) != good_edge_len:
        raise BadEdgeError(f"Edge ${BadEdgeError.EDGE_KEY} doesn't connect "
                           "exactly 2 functional units.", edge)

    processor.add_edge(*_get_std_edge(edge, unit_registry))
    old_edge = edge_registry.get(edge)

    if old_edge is None:
        edge_registry.add(edge)
    else:
        logging.warning(
            "Edge %s previously added as %s, ignoring...", edge, old_edge)


def _add_instr(instr_registry, cap_registry, instr, cap):
    """Add an instruction to the instruction set.

    `instr_registry` is the store of previously added instructions.
    `cap_registry` is the store of supported capabilities.
    `instr` is the instruction to add.
    `cap` is the instruction capability.
    The function returns a tuple of the upper-case instruction and its
    capability.

    """
    _chk_instr(instr, instr_registry)
    instr_registry.add(instr)
    return instr.raw_str.upper(), _get_cap_name(cap, cap_registry)


def _add_new_cap(cap, cap_list, unit_cap_reg, global_cap_reg):
    """Add a new capability to the given list and registry.

    `cap` is the capability to add.
    `cap_list` is the list of capabilities in a unit.
    `unit_cap_reg` is the store of previously added capabilities in the
                   unit whose capability list is given.
    `global_cap_reg` is the store of added capabilities across all units
                     so far.

    """
    std_cap = global_cap_reg.get(cap)

    if std_cap is None:
        std_cap = _add_to_set(global_cap_reg, cap)
    elif std_cap.name.raw_str != cap.name.raw_str:
        logging.warning("Capability %s in unit %s previously defined as %s in "
                        "unit %s, using original definition...", cap.name,
                        cap.unit, std_cap.name, std_cap.unit)

    cap_list.append(std_cap.name)
    unit_cap_reg.add(cap.name)


def _add_port_link(graph, old_port, new_port, link):
    """Add a link between old and new ports.

    `graph` is the graph containing ports.
    `old_port` is the old port.
    `new_port` is the new port.
    `link` is the link connecting the two ports.

    """
    graph.nodes[new_port][_UNIT_WIDTH_KEY] += graph.nodes[old_port][
        _UNIT_WIDTH_KEY]
    graph.add_edge(*link)


def _add_src_path():
    """Add the source path to the python search path."""
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


def _add_to_set(elem_set, elem):
    """Add an element to the given set.

    `elem_set` is the set to add the element to.
    `elem` is the element to add.

    """
    elem_set.add(elem)
    return elem


def _add_unit(processor, unit, unit_registry, cap_registry):
    """Add a functional unit to a processor.

    `processor` is the processor to add the unit to.
    `unit` is the functional unit to add.
    `unit_registry` is the store of previously added units.
    `cap_registry` is the store of previously added capabilities.

    """
    unit_name = ICaseString(unit[_UNIT_NAME_KEY])
    _chk_unit_name(unit_name, unit_registry)
    _chk_unit_width(unit)
    unit_locks = map(lambda attr: (attr, unit.get(attr, False)),
                     [_UNIT_RLOCK_KEY, _UNIT_WLOCK_KEY])
    processor.add_node(unit_name, **concat_dicts(
        {_UNIT_WIDTH_KEY: unit[_UNIT_WIDTH_KEY],
         _UNIT_CAPS_KEY: _load_caps(unit, cap_registry)}, dict(unit_locks)))
    unit_registry.add(unit_name)


def _aug_out_ports(processor, out_ports):
    """Unify the output ports in the processor.

    `processor` is the processor containing the output ports.
    `out_ports` are the output ports to weld.
    The function connects several output ports into a single output port
    and returns that single port.

    """
    return _aug_terminals(processor, out_ports, lambda *outputs: outputs)


def _aug_terminals(graph, ports, edge_func):
    """Unify terminals indicated by degrees in the graph.

    `graph` is the graph containing terminals.
    `ports` are the terminals to unify.
    `edge_func` is the creation function for edges connecting old
                terminals to the new one. It takes as parameters the old
                and the new terminals in order and returns a tuple
                representing the directed edge between the two.
    The function tries to connect several terminals into a single new
    terminal. The function returns the newly added port.

    """
    return ports[0] if len(ports) == 1 else _unify_ports(
        graph, ports, edge_func)


def _cap_in_edge(processor, capability, edge):
    """Check if the given capability is supported by the edge.

    `processor` is the processor containing the edge.
    `capability` is the capability to check.
    `edge` is the edge to check.

    """
    return all(map(lambda unit:
                   capability in processor.nodes[unit][_UNIT_CAPS_KEY], edge))


def _chk_cap_flow(
        anal_graph, capability_info, in_ports, out_ports, port_name_func):
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
    unit_anal_map = dict(
        map(lambda anal_entry: (anal_entry[1][_OLD_NODE_KEY], anal_entry[0]),
            anal_graph.nodes(True)))
    unified_out = _aug_out_ports(
        anal_graph, [unit_anal_map[port] for port in out_ports])
    unified_out = _split_nodes(anal_graph)[unified_out]
    _dist_edge_caps(anal_graph)

    for cur_port in in_ports:
        _chk_unit_flow(networkx.maximum_flow_value(
            anal_graph, unit_anal_map[cur_port], unified_out), capability_info,
                       ComponentInfo(cur_port, port_name_func(cur_port)))


def _chk_caps_flow(processor):
    """Check the flow capacity for every capability in the processor.

    `processor` is the processor to check.
    The function raises a BlockedCapError if any capability through any
    supporting input port can't flow with full or partial capacity from
    this input port to the output ports.

    """
    cap_units = _get_cap_units(processor)
    out_ports = list(_get_out_ports(processor))

    for cap, in_ports in cap_units:
        _chk_cap_flow(_get_anal_graph(_make_cap_graph(processor, cap)),
                      ComponentInfo(cap, "Capability " + cap), in_ports,
                      out_ports, lambda port: "port " + port)


def _chk_cycles(processor):
    """Check the given processor for cycles.

    `processor` is the processor to check.
    The function raises a NetworkXUnfeasible if the processor isn't a
    DAG.

    """
    if not networkx.is_directed_acyclic_graph(processor):
        raise networkx.NetworkXUnfeasible()


def _chk_edge(processor, edge):
    """Check if the edge is useful.

    `processor` is the processor containing the edge.
    `edge` is the edge to check.
    The function removes the given edge if it isn't needed. It returns
    the common capabilities between the units connected by the edge.

    """
    common_caps = processor.nodes[edge[1]][_UNIT_CAPS_KEY].intersection(
        processor.nodes[edge[0]][_UNIT_CAPS_KEY])

    if not common_caps:
        _rm_dummy_edge(processor, edge)

    return common_caps


def _chk_flow(processor):
    """Check the flow of every supported capability in every input port.

    `processor` is the processor to check whose capability flow.
    The function tests the flow of every supported capability through
    every compatible input port. If any capability through any input
    port can't flow with full or partial capacity from this input port
    to the output ports, the function raises a BlockedCapError.

    """
    if processor.number_of_nodes() > 1:
        _chk_caps_flow(processor)


def _chk_instr(instr, instr_registry):
    """Check the given instruction.

    `instr` is the instruction.
    `instr_registry` is the store of previously added instructions.
    The function raises a DupElemError if the same instruction was previously
    added to the instruction store.

    """
    old_instr = instr_registry.get(instr)

    if old_instr is not None:
        raise DupElemError(
            f"Instruction ${DupElemError.NEW_ELEM_KEY} previously added as "
            f"${DupElemError.OLD_ELEM_KEY}", old_instr, instr)


def _chk_multi_lock(processor):
    """Check if the processor has paths with multiple locks.

    `processor` is the processor to check for multi-lock paths.
    The function raises a MultiLockError if any paths with multiple
    locks exist.

    """
    post_ord = dfs_postorder_nodes(processor)
    path_locks = {}

    for unit in post_ord:
        _chk_path_locks(unit, processor, path_locks)


def _chk_non_empty(processor, in_ports):
    """Check if the processor still has input ports.

    `processor` is the processor to check.
    `in_ports` are the processor original input ports.
    The function raises an EmptyProcError if no input ports still exist.

    """
    try:
        next(filter(lambda port: port in processor, in_ports))
    except StopIteration:  # No ports exist.
        raise exception.EmptyProcError("No input ports found")


def _chk_path_locks(start, processor, path_locks):
    """Check if paths from the given start unit contains multiple locks.

    `start` is the starting unit of paths to check.
    `processor` is the processor containing the start unit.
    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    The function raises a MultiLockError if any paths originating from
    the given unit have multiple locks.

    """
    succ_lst = list(processor.successors(start))
    path_locks[start] = _SatInfo(
        _init_path_lock(
            processor.nodes[start][_UNIT_RLOCK_KEY], succ_lst, _get_read_path,
            path_locks), _init_path_lock(processor.nodes[start][
                _UNIT_WLOCK_KEY], succ_lst, _get_write_path, path_locks))

    for path_desc in [_PathDescriptor(_get_read_path, "read"),
                      _PathDescriptor(_get_write_path, "write")]:
        if path_desc.selector(path_locks[start]).next_node:
            _accum_locks(path_locks, path_desc, start)


def _chk_terminals(processor, orig_port_info):
    """Check if new terminals have appeared after optimization.

    `processor` is the processor to check.
    `orig_port_info` is the original port information(before
                     optimization).
    The function removes spurious output ports that might have appeared
    after trimming actions during optimization.

    """
    all_out_ports = _get_out_ports(processor)
    new_out_ports = [
        port for port in all_out_ports if port not in orig_port_info.out_ports]

    for out_port in new_out_ports:
        _rm_dead_end(processor, out_port, orig_port_info.in_ports)


def _chk_unit_flow(min_width, capability_info, port_info):
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
            f"${BlockedCapError.PORT_KEY}", exception.CapPortInfo(
                capability_info, port_info))


def _chk_unit_name(name, name_registry):
    """Check the given unit name.

    `name` is the unit name.
    `name_registry` is the name store of previously added units.
    The function raises a DupElemError if a unit with the same name was
    previously added to the processor.

    """
    old_name = name_registry.get(name)

    if old_name is not None:
        raise DupElemError(
            f"Functional unit ${DupElemError.NEW_ELEM_KEY} previously added as"
            f" ${DupElemError.OLD_ELEM_KEY}", old_name, name)


def _chk_unit_width(unit):
    """Check the given unit width.

    `unit` is the unit to load whose width.
    The function raises a BadWidthError if the width isn't positive.

    """
    if unit[_UNIT_WIDTH_KEY] <= 0:
        raise BadWidthError(f"Functional unit ${BadWidthError.UNIT_KEY} has a "
                            f"bad width ${BadWidthError.WIDTH_KEY}.",
                            *itemgetter(_UNIT_NAME_KEY, _UNIT_WIDTH_KEY)(unit))


def _clean_struct(processor):
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


def _clean_unit(processor, unit):
    """Clean the given unit properties.

    `processor` is the processor containing the unit.
    `unit` is the unit to clean whose properties.
    The function restricts the capabilities of the given unit to only
    those supported by its predecessors. It also removes incoming edges
    coming from a predecessor unit having no capabilities in common with
    the given unit.

    """
    processor.nodes[unit][_UNIT_CAPS_KEY] = frozenset(
        processor.nodes[unit][_UNIT_CAPS_KEY])
    pred_caps = map(lambda edge: _chk_edge(processor, edge),
                    list(processor.in_edges(unit)))
    processor.nodes[unit][_UNIT_CAPS_KEY] = frozenset().union(*pred_caps)


def _coll_cap_edges(graph):
    """Collect capping edges from the given graph.

    `graph` is the graph to collect edges from.
    The function returns capping edges. A capping edge is the sole edge
    on either side of a node that determines the maximum flow through
    the node.

    """
    out_degrees = graph.out_degree()
    cap_edges = map(lambda in_deg: _get_cap_edge(
        graph.in_edges(in_deg[0]), graph.out_edges(in_deg[0])),
                    filter(lambda in_deg: in_deg[1] == 1 or
                           out_degrees[in_deg[0]] == 1, graph.in_degree()))
    return frozenset(cap_edges)


def _create_graph(hw_units, links):
    """Create a data flow graph for a processor.

    `hw_units` are the processor functional units.
    `links` are the connections between the functional units.
    The function returns a directed graph representing the reverse data
    flow through the processor functional units.

    """
    flow_graph = DiGraph()
    unit_registry = SelfIndexSet()
    edge_registry = IndexedSet(
        lambda edge: tuple(_get_edge_units(edge, unit_registry)))
    cap_registry = IndexedSet(lambda cap: cap.name)

    for cur_unit in hw_units:
        _add_unit(flow_graph, cur_unit, unit_registry, cap_registry)

    for cur_link in links:
        _add_edge(flow_graph, cur_link, unit_registry, edge_registry)

    return flow_graph


def _create_isa(isa_dict, cap_registry):
    """Create an instruction set in the given ISA dictionary.

    `isa_dict` is the ISA dictionary to normalize.
    `cap_registry` is the store of supported capabilities.
    The function returns the ISA dictionary with upper-case instructions
    and standard capability names.

    """
    instr_registry = SelfIndexSet()
    isa_spec = map(
        lambda isa_entry: map(ICaseString, isa_entry), isa_dict.items())
    return dict(map(lambda isa_entry: _add_instr(
        instr_registry, cap_registry, *isa_entry), isa_spec))


def _create_path(path_locks, path_sel, start):
    """Construct the path containing multiple locks.

    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    `path_sel` is the path selection function.
    `start` is the starting unit of paths to check.

    """
    multiLockPath = []
    cur_node = start

    while cur_node:
        cur_node = path_sel(path_locks[
            _update_path(multiLockPath, cur_node, path_locks)]).next_node

    return multiLockPath


def _dist_edge_caps(graph):
    """Distribute capacities over edges as needed.

    `graph` is the graph containing edges.
    The function distributes capacities over capping edges.

    """
    _set_capacities(graph, _coll_cap_edges(graph))


def _get_anal_graph(processor):
    """Create a processor bus width analysis graph.

    `processor` is the processor to build an analysis graph from.

    """
    width_graph = DiGraph()
    hw_units = enumerate(processor)
    new_nodes = {}

    for idx, unit in hw_units:
        _update_graph(idx, unit, processor, width_graph, new_nodes)

    width_graph.add_edges_from(
        map(lambda edge: itemgetter(*edge)(new_nodes), processor.edges))
    return width_graph


def _get_cap_edge(in_edges, out_edges):
    """Select the capping edge.

    `in_edges` is an iterator over input edges.
    `out_edges` is an iterator over output edges.
    A capping edge is the sole edge on either side of a node that
    determines the maximum flow through the node. Either the input edges
    or the output edges must contain exactly one edge.

    """
    return _single_edge(iter(in_edges)) or next(iter(out_edges))


def _get_cap_name(capability, cap_registry):
    """Return a supported capability name.

    `capability` is the name of the capability to validate.
    `cap_registry` is the store of supported capabilities.
    The function raises an UndefElemError if no capability with this
    name is supported, otherwise returns the supported capability name.

    """
    std_cap = cap_registry.get(capability)

    if std_cap is None:
        raise UndefElemError(
            f"Unsupported capability ${UndefElemError.ELEM_KEY}", capability)

    return std_cap


def _get_cap_units(processor):
    """Create a mapping between capabilities and supporting input ports.

    `processor` is the processor to create a capability-port map for.
    The function returns an iterable of tuples; each tuple represents a
    capability and its supporting units.

    """
    cap_unit_map = {}
    in_ports = _get_in_ports(processor)

    for cur_port in in_ports:
        for cur_cap in processor.nodes[cur_port][_UNIT_CAPS_KEY]:
            cap_unit_map.setdefault(cur_cap, []).append(cur_port)

    return cap_unit_map.items()


def _get_edge_units(edge, unit_registry):
    """Return the units of an edge.

    `edge` is the edge to retrieve whose units.
    `unit_registry` is the store of units.

    """
    return map(lambda unit: unit_registry.get(ICaseString(unit)), edge)


def _get_in_ports(processor):
    """Find the input ports.

    `processor` is the processor to find whose input ports.
    The function returns an iterator over the processor input ports.

    """
    return _get_ports(processor.in_degree())


def _get_out_ports(processor):
    """Find the output ports.

    `processor` is the processor to find whose output ports.
    The function returns an iterator over the processor output ports.

    """
    return _get_ports(processor.out_degree())


def _get_ports(degrees):
    """Find the ports with respect to the given degrees.

    `degrees` are the degrees of all units.
    A port is a unit with zero degree.

    """
    return map(itemgetter(0), itertools.filterfalse(itemgetter(1), degrees))


def _get_preds(processor, unit, unit_map):
    """Retrieve the predecessor units of the given unit.

    `processor` is the processor containing the unit.
    `unit` is the unit to retrieve whose predecessors.
    `unit_map` is the mapping between names and units.
    The function returns an iterable of predecessor units.

    """
    return map(unit_map.get, processor.predecessors(unit))


def _get_read_path(sat_info):
    """Retrieve the read path from the given saturation information.

    `sat_info` is the saturation information.

    """
    return sat_info.read_path


def _get_std_edge(edge, unit_registry):
    """Return a validated edge.

    `edge` is the edge to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if an undefined unit is
    encountered.

    """
    return map(
        lambda unit: _get_unit_name(ICaseString(unit), unit_registry), edge)


def _get_unit_entry(name, attrs):
    """Create a unit map entry from the given attributes.

    `name` is the unit name.
    `attrs` are the unit attribute dictionary.
    The function returns a tuple of the unit name and model.

    """
    lock_info = units.LockInfo(
        *itemgetter(_UNIT_RLOCK_KEY, _UNIT_WLOCK_KEY)(attrs))
    return name, UnitModel(name, *itemgetter(_UNIT_WIDTH_KEY, _UNIT_CAPS_KEY)(
        attrs) + (lock_info,))


def _get_unit_name(unit, unit_registry):
    """Return a validated unit name.

    `unit` is the name of the unit to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if no unit exists with this
    name, otherwise returns the validated unit name.

    """
    std_name = unit_registry.get(unit)

    if std_name is None:
        raise UndefElemError(
            f"Undefined functional unit ${UndefElemError.ELEM_KEY}", unit)

    return std_name


def _get_write_path(sat_info):
    """Retrieve the write path from the given saturation information.

    `sat_info` is the saturation information.

    """
    return sat_info.write_path


def _init_cap_reg(capabilities):
    """Initialize a capability registry.

    `capabilities` are the unique capabilities to initially insert into
                   the registry.
    The function returns a capability registry containing the given
    unique capabilities.

    """
    cap_registry = IndexedSet(lambda cap: cap)

    for cap in capabilities:
        cap_registry.add(cap)

    return cap_registry


def _init_path_lock(unit_lock, succ_lst, path_sel, path_locks):
    """Initialize the path lock information.

    `unit_lock` is the lock status of the unit.
    `succ_lst` is the list of successor units.
    `path_sel` is the path selection function.
    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.

    """
    return _PathLockInfo(
        1 if unit_lock else 0, max(succ_lst, default=None, key=lambda succ:
                                   path_sel(path_locks[succ]).num_of_locks))


def _load_caps(unit, cap_registry):
    """Load the given unit capabilities.

    `unit` is the unit to load whose capabilities.
    `cap_registry` is the store of previously added capabilities.
    The function returns a list of loaded capabilities.

    """
    cap_list = []
    unit_cap_reg = SelfIndexSet()

    for cur_cap in unit[_UNIT_CAPS_KEY]:
        _add_capability(unit[_UNIT_NAME_KEY], ICaseString(cur_cap), cap_list,
                        unit_cap_reg, cap_registry)

    return cap_list


def _make_cap_graph(processor, capability):
    """Create a graph condensed for the given capability.

    `processor` is the processor to create a graph from.
    `capability` is the capability to consider while constructing the
                 graph.
    The function creates a graph with all units in the original
    processor but only with edges connecting units having the given
    capability in common.

    """
    cap_graph = DiGraph(
        filter(lambda edge: _cap_in_edge(processor, capability, edge),
               processor.edges))
    cap_graph.add_nodes_from(processor.nodes(True))
    return cap_graph


def _make_processor(proc_graph):
    """Create a processor description from the given units.

    `proc_desc` is the processor graph.

    """
    post_ord = _post_order(proc_graph)
    in_out_ports = []
    in_ports = []
    internal_units = []
    out_ports = []
    in_degrees = proc_graph.in_degree()
    out_degrees = proc_graph.out_degree()

    for unit in post_ord:
        if in_degrees[unit.model.name] and out_degrees[unit.model.name]:
            internal_units.append(unit)
        elif in_degrees[unit.model.name]:
            out_ports.append(unit)
        elif out_degrees[unit.model.name]:
            in_ports.append(unit.model)
        elif not in_degrees[unit.model.name]:
            in_out_ports.append(unit.model)

    return ProcessorDesc(in_ports, out_ports, in_out_ports, internal_units)


def _mov_out_link(graph, link, new_node):
    """Move an outgoing link from an old node to a new one.

    `graph` is the graph containing the nodes.
    `link` is the outgoing link to move.
    `new_node` is the node to move the outgoing link to.

    """
    graph.add_edge(new_node, link[1])
    graph.remove_edge(*link)


def _mov_out_links(graph, out_links, new_node):
    """Move outgoing links from an old node to a new one.

    `graph` is the graph containing the nodes.
    `out_links` are the outgoing links to move.
    `new_node` is the node to move the outgoing links to.

    """
    for cur_link in out_links:
        _mov_out_link(graph, cur_link, new_node)


def _post_order(graph):
    """Create a post-order for the given processor.

    `graph` is the processor.
    The function returns a list of the processor functional units in
    post-order.

    """
    unit_map = dict(
        map(lambda unit: _get_unit_entry(unit, graph.nodes[unit]), graph))
    return map(lambda name: FuncUnit(unit_map[name], _get_preds(
        graph, name, unit_map)), dfs_postorder_nodes(graph))


def _prep_proc_desc(processor):
    """Prepare the given processor.

    `processor` is the processor to prepare.
    The function makes some preliminary checks against the processor and
    optimizes its structure by trying to only keep the effective units
    needed in a typical program execution. It raises an EmptyProcError
    if the processor doesn't contain any units, a NetworkXUnfeasible if
    the processor isn't a DAG, and a BlockedCapError if input width
    exceeds the minimum bus width.

    """
    _chk_cycles(processor)
    port_info = _PortGroup(processor)
    _clean_struct(processor)
    _rm_empty_units(processor)
    _chk_terminals(processor, port_info)
    _chk_non_empty(processor, port_info.in_ports)
    _chk_flow(processor)
    _chk_multi_lock(processor)


def _rm_dead_end(processor, dead_end, in_ports):
    """Remove a dead end from the given processor.

    `processor` is the processor to remove the dead end from.
    `dead_end` is the dead end to remove.
    `in_ports` are the processor original input ports.
    A dead end is a port that looks like an output port after
    optimization actions have cut it off real output ports.

    """
    if dead_end in in_ports:  # an in-port turned in-out port
        raise DeadInputError("No feasible path found from input port "
                             f"${DeadInputError.PORT_KEY} to any output ports",
                             dead_end)

    logging.warning("Dead end detected at unit %s, removing...", dead_end)
    processor.remove_node(dead_end)


def _rm_dummy_edge(processor, edge):
    """Remove an edge from the given processor.

    `processor` is the processor to remove the edge from.
    `edge` is the edge to remove.

    """
    logging.warning("Units %s and %s have no capabilities in common, "
                    "removing connecting edge...", *edge)
    processor.remove_edge(*edge)


def _rm_empty_unit(processor, unit):
    """Remove a unit from the given processor.

    `processor` is the processor to remove the unit from.
    `unit` is the unit to remove.

    """
    logging.warning("No capabilities defined for unit %s, removing...", unit)
    processor.remove_node(unit)


def _rm_empty_units(processor):
    """Remove empty units from the given processor.

    `processor` is the processor to clean.
    The function removes units with no capabilities from the processor.

    """
    unit_entries = list(processor.nodes(True))

    for unit, attrs in unit_entries:
        if not attrs[_UNIT_CAPS_KEY]:
            _rm_empty_unit(processor, unit)


def _set_capacities(graph, cap_edges):
    """Assign capacities to capping edges.

    `graph` is the graph containing edges.
    `cap_edges` are the capping edges.

    """
    for cur_edge in cap_edges:
        graph[cur_edge[0]][cur_edge[1]]["capacity"] = min(
            map(lambda unit: graph.nodes[unit][_UNIT_WIDTH_KEY], cur_edge))


def _single_edge(edges):
    """Select the one and only edge.

    `edges` are an iterator over edges. Must contain a single edge.
    The function returns the only edge in the given edges, or None if
    the edges don't contain exactly a single edge.

    """
    try:
        only_edge = next(edges)
        try:
            next(edges)
        except StopIteration:  # only one edge
            return only_edge
    except StopIteration:  # Input edges are empty.
        pass


def _split_node(graph, old_node, new_node):
    """Split a node into old and new ones.

    `graph` is the graph containing the node to be split.
    `old_node` is the existing node.
    `new_node` is the node added after splitting.
    The function returns the new node.

    """
    graph.add_node(
        new_node, **{_UNIT_WIDTH_KEY: graph.nodes[old_node][_UNIT_WIDTH_KEY]})
    _mov_out_links(graph, list(graph.out_edges(old_node)), new_node)
    graph.add_edge(old_node, new_node)
    return new_node


def _split_nodes(graph):
    """Split nodes in the given graph as necessary.

    `graph` is the graph containing nodes.
    The function splits nodes having multiple links on one side and a
    non-capping link on the other. A link on one side is capping if it's
    the only link on this side.
    The function returns a dictionary mapping each unit to its output
    twin(if one was created) or itself if it wasn't split.

    """
    out_degrees = graph.out_degree()
    out_twins = map(
        lambda in_deg_item:
        (in_deg_item[0],
         _split_node(graph, in_deg_item[0], len(out_degrees) + in_deg_item[
            0]) if in_deg_item[1] != 1 and out_degrees[in_deg_item[0]] != 1 and
         (in_deg_item[1] or out_degrees[in_deg_item[0]]) else in_deg_item[0]),
        list(graph.in_degree()))
    return dict(out_twins)


def _unify_ports(graph, ports, edge_func):
    """Unify ports in the graph.

    `graph` is the graph containing terminals.
    `ports` are the ports to unify.
    `edge_func` is the creation function for edges connecting old
                terminals to the new one. It takes as parameters the old
                and the new terminals in order and returns a tuple
                representing the directed edge between the two.
    The function returns the new port.

    """
    unified_port = graph.number_of_nodes()
    graph.add_node(unified_port, **{_UNIT_WIDTH_KEY: 0})

    for cur_port in ports:
        _add_port_link(
            graph, cur_port, unified_port, edge_func(cur_port, unified_port))

    return unified_port


def _update_graph(idx, unit, processor, width_graph, unit_idx_map):
    """Update width graph structures.

    `idx` is the unit index.
    `unit` is the unit name.
    `processor` is the original processor.
    `width_graph` is the bus width analysis graph.
    `unit_idx_map` is the mapping between unit names and indices.

    """
    width_graph.add_node(
        idx, **concat_dicts(processor.nodes[unit], {_OLD_NODE_KEY: unit}))
    unit_idx_map[unit] = idx


def _update_path(multiLockPath, new_node, path_locks):
    """Update the path containing multiple locks.

    `multiLockPath` is the multi-lock path to update.
    `new_node` is the node to append to the path.
    `path_locks` are the map from a unit to the information of the path
                 with maximum locks.
    The function appends the given node and returns it.

    """
    multiLockPath.append(new_node)
    return new_node


_add_src_path()
