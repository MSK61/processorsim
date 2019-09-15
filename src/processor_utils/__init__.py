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
# environment:  Visual Studdio Code 1.38.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import dataclasses
import functools
import logging
from operator import itemgetter
import os
import sys
import typing
from typing import Tuple
import networkx
import container_utils
from container_utils import IndexedSet, SelfIndexSet
from errors import UndefElemError
from str_utils import ICaseString
from . import checks
from .exception import BadEdgeError, BadWidthError, DupElemError
from . import optimization
from . import port_defs
from . import units
from .units import FuncUnit, UNIT_CAPS_KEY, UnitModel, UNIT_NAME_KEY, \
    UNIT_RLOCK_KEY, UNIT_WIDTH_KEY, UNIT_WLOCK_KEY
__all__ = ["exception", "get_abilities", "load_isa", "load_proc_desc",
           "ProcessorDesc", "units"]


@dataclasses.dataclass
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


class _CapabilityInfo(typing.NamedTuple):

    """Unit capability information"""

    name: ICaseString

    unit: str


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

    if old_cap:
        logging.warning(
            "Capability %s previously added as %s for unit %s, ignoring...",
            cap, old_cap, unit)
    else:
        _add_new_cap(
            _CapabilityInfo(cap, unit), cap_list, unit_cap_reg, global_cap_reg)


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

    if old_edge:
        logging.warning(
            "Edge %s previously added as %s, ignoring...", edge, old_edge)
    else:
        edge_registry.add(edge)


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
    std_cap = container_utils.get_from_set(global_cap_reg, cap)

    if std_cap.name.raw_str != cap.name.raw_str:
        logging.warning("Capability %s in unit %s previously defined as %s in "
                        "unit %s, using original definition...", cap.name,
                        cap.unit, std_cap.name, std_cap.unit)

    cap_list.append(std_cap.name)
    unit_cap_reg.add(cap.name)


def _add_src_path():
    """Add the source path to the python search path."""
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


def _add_unit(processor, unit, unit_registry, cap_registry):
    """Add a functional unit to a processor.

    `processor` is the processor to add the unit to.
    `unit` is the functional unit to add.
    `unit_registry` is the store of previously added units.
    `cap_registry` is the store of previously added capabilities.

    """
    unit_name = ICaseString(unit[UNIT_NAME_KEY])
    _chk_unit_name(unit_name, unit_registry)
    _chk_unit_width(unit)
    unit_locks = map(lambda attr: (attr, unit.get(attr, False)),
                     [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY])
    processor.add_node(unit_name, **container_utils.concat_dicts(
        {UNIT_WIDTH_KEY: unit[UNIT_WIDTH_KEY],
         UNIT_CAPS_KEY: _load_caps(unit, cap_registry)}, dict(unit_locks)))
    unit_registry.add(unit_name)


def _chk_instr(instr, instr_registry):
    """Check the given instruction.

    `instr` is the instruction.
    `instr_registry` is the store of previously added instructions.
    The function raises a DupElemError if the same instruction was previously
    added to the instruction store.

    """
    old_instr = instr_registry.get(instr)

    if old_instr:
        raise DupElemError(
            f"Instruction ${DupElemError.NEW_ELEM_KEY} previously added as "
            f"${DupElemError.OLD_ELEM_KEY}", old_instr, instr)


def _chk_unit_name(name, name_registry):
    """Check the given unit name.

    `name` is the unit name.
    `name_registry` is the name store of previously added units.
    The function raises a DupElemError if a unit with the same name was
    previously added to the processor.

    """
    old_name = name_registry.get(name)

    if old_name:
        raise DupElemError(
            f"Functional unit ${DupElemError.NEW_ELEM_KEY} previously added as"
            f" ${DupElemError.OLD_ELEM_KEY}", old_name, name)


def _chk_unit_width(unit):
    """Check the given unit width.

    `unit` is the unit to load whose width.
    The function raises a BadWidthError if the width isn't positive.

    """
    if unit[UNIT_WIDTH_KEY] <= 0:
        raise BadWidthError(f"Functional unit ${BadWidthError.UNIT_KEY} has a "
                            f"bad width ${BadWidthError.WIDTH_KEY}.",
                            *itemgetter(UNIT_NAME_KEY, UNIT_WIDTH_KEY)(unit))


def _create_graph(hw_units, links):
    """Create a data flow graph for a processor.

    `hw_units` are the processor functional units.
    `links` are the connections between the functional units.
    The function returns a directed graph representing the reverse data
    flow through the processor functional units.

    """
    flow_graph = networkx.DiGraph()
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


def _get_cap_name(capability, cap_registry):
    """Return a supported capability name.

    `capability` is the name of the capability to validate.
    `cap_registry` is the store of supported capabilities.
    The function raises an UndefElemError if no capability with this
    name is supported, otherwise returns the supported capability name.

    """
    std_cap = cap_registry.get(capability)

    if not std_cap:
        raise UndefElemError(
            f"Unsupported capability ${UndefElemError.ELEM_KEY}", capability)

    return std_cap


def _get_edge_units(edge, unit_registry):
    """Return the units of an edge.

    `edge` is the edge to retrieve whose units.
    `unit_registry` is the store of units.

    """
    return map(lambda unit: unit_registry.get(ICaseString(unit)), edge)


def _get_preds(processor, unit, unit_map):
    """Retrieve the predecessor units of the given unit.

    `processor` is the processor containing the unit.
    `unit` is the unit to retrieve whose predecessors.
    `unit_map` is the mapping between names and units.
    The function returns an iterable of predecessor units.

    """
    return map(unit_map.get, processor.predecessors(unit))


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
        *itemgetter(UNIT_RLOCK_KEY, UNIT_WLOCK_KEY)(attrs))
    return name, UnitModel(name, *(
        itemgetter(UNIT_WIDTH_KEY, UNIT_CAPS_KEY)(attrs) + (lock_info,)))


def _get_unit_name(unit, unit_registry):
    """Return a validated unit name.

    `unit` is the name of the unit to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if no unit exists with this
    name, otherwise returns the validated unit name.

    """
    std_name = unit_registry.get(unit)

    if not std_name:
        raise UndefElemError(
            f"Undefined functional unit ${UndefElemError.ELEM_KEY}", unit)

    return std_name


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


def _load_caps(unit, cap_registry):
    """Load the given unit capabilities.

    `unit` is the unit to load whose capabilities.
    `cap_registry` is the store of previously added capabilities.
    The function returns a list of loaded capabilities.

    """
    cap_list = []
    unit_cap_reg = SelfIndexSet()

    for cur_cap in unit[UNIT_CAPS_KEY]:
        _add_capability(unit[UNIT_NAME_KEY], ICaseString(cur_cap), cap_list,
                        unit_cap_reg, cap_registry)

    return cap_list


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


def _post_order(graph):
    """Create a post-order for the given processor.

    `graph` is the processor.
    The function returns a list of the processor functional units in
    post-order.

    """
    unit_map = dict(
        map(lambda unit: _get_unit_entry(unit, graph.nodes[unit]), graph))
    return map(lambda name: FuncUnit(unit_map[name], _get_preds(
        graph, name, unit_map)), networkx.dfs_postorder_nodes(graph))


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
    checks.chk_cycles(processor)
    port_info = port_defs.PortGroup(processor)
    optimization.clean_struct(processor)
    optimization.rm_empty_units(processor)
    optimization.chk_terminals(processor, port_info)
    checks.chk_non_empty(processor, port_info.in_ports)
    checks.chk_caps(processor)


_add_src_path()
