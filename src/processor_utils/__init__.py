# -*- coding: utf-8 -*-

"""processor_utils package"""

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
# file:         __init__.py
#
# function:     processor_utils package
#
# description:  processor_utils package export file
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

from itertools import chain
from logging import warning
import operator
import os
import sys
import typing
from typing import (
    Any,
    Collection,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    Tuple,
)

import attr
from fastcore.foundation import map_ex, maps, Self
import networkx
from networkx import DiGraph, Graph

import container_utils
from container_utils import IndexedSet, SelfIndexSet
from errors import UndefElemError
from str_utils import ICaseString
from . import _checks, _optimization, _port_defs, units
from .exception import BadEdgeError, BadWidthError, DupElemError
from .units import (
    FuncUnit,
    UNIT_CAPS_KEY,
    UNIT_MEM_KEY,
    UnitModel,
    UNIT_NAME_KEY,
    UNIT_RLOCK_KEY,
    UNIT_WIDTH_KEY,
    UNIT_WLOCK_KEY,
)

_T = typing.TypeVar("_T")
_UNIT_KEY: typing.Final = "unit"


def load_isa(
    raw_isa: Iterable[Tuple[str, str]], capabilities: Iterable[object]
) -> Dict[str, object]:
    """Transform the given raw description into an instruction set.

    `raw_isa` is the raw description to extract an instruction set from.
    `capabilities` are the supported unique capabilities.
    The function returns a mapping between upper-case supported
    instructions and their capabilities.

    """
    return _create_isa(raw_isa, _init_cap_reg(capabilities))


@attr.s(auto_attribs=True, frozen=True)
class _CapabilityInfo:

    """Unit capability information"""

    name: ICaseString

    unit: object


def _add_capability(
    unit: object,
    cap: ICaseString,
    cap_list: MutableSequence[object],
    unit_cap_reg: SelfIndexSet[object],
    global_cap_reg: IndexedSet[_CapabilityInfo],
) -> None:
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
        warning(
            "Capability %s previously added as %s for unit %s, ignoring...",
            cap,
            old_cap,
            unit,
        )
    else:
        _add_new_cap(
            _CapabilityInfo(cap, unit), cap_list, unit_cap_reg, global_cap_reg
        )


def _add_edge(
    processor: Graph,
    edge: Collection[str],
    unit_registry: SelfIndexSet[object],
    edge_registry: IndexedSet[Collection[str]],
) -> None:
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
        raise BadEdgeError(
            f"Edge ${BadEdgeError.EDGE_KEY} doesn't connect exactly "
            f"{good_edge_len} functional units.",
            edge,
        )

    processor.add_edge(*(_get_std_edge(edge, unit_registry)))
    old_edge = edge_registry.get(edge)

    if old_edge:
        warning("Edge %s previously added as %s, ignoring...", edge, old_edge)
    else:
        edge_registry.add(edge)


def _add_instr(
    instr_registry: SelfIndexSet[object],
    cap_registry: SelfIndexSet[object],
    instr: object,
    cap: object,
) -> object:
    """Add an instruction to the instruction set.

    `instr_registry` is the store of previously added instructions.
    `cap_registry` is the store of supported capabilities.
    `instr` is the instruction to add.
    `cap` is the instruction capability.
    The function returns the instruction capability.

    """
    _chk_instr(instr, instr_registry)
    instr_registry.add(instr)
    return _get_cap_name(cap, cap_registry)


def _add_new_cap(
    cap: _CapabilityInfo,
    cap_list: MutableSequence[object],
    unit_cap_reg: SelfIndexSet[object],
    global_cap_reg: IndexedSet[_CapabilityInfo],
) -> None:
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
        warning(
            "Capability %s in unit %s previously defined as %s in unit %s, "
            "using original definition...",
            cap.name,
            cap.unit,
            std_cap.name,
            std_cap.unit,
        )

    cap_list.append(std_cap.name)
    unit_cap_reg.add(cap.name)


def _add_src_path() -> None:
    """Add the source path to the python search path."""
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


def _add_unit(
    processor: Graph,
    unit: Mapping[object, Any],
    unit_registry: SelfIndexSet[object],
    cap_registry: IndexedSet[_CapabilityInfo],
) -> None:
    """Add a functional unit to a processor.

    `processor` is the processor to add the unit to.
    `unit` is the functional unit to add.
    `unit_registry` is the store of previously added units.
    `cap_registry` is the store of previously added capabilities.

    """
    unit_name = ICaseString(unit[UNIT_NAME_KEY])
    _chk_unit_name(unit_name, unit_registry)
    _chk_unit_width(unit)
    processor.add_node(
        unit_name,
        **{
            UNIT_WIDTH_KEY: unit[UNIT_WIDTH_KEY],
            UNIT_CAPS_KEY: _load_caps(unit, cap_registry),
            UNIT_MEM_KEY: _load_mem_acl(unit, cap_registry),
        },
        **{
            cur_attr: unit.get(cur_attr, False)
            for cur_attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
        },
    )
    unit_registry.add(unit_name)


def _chk_instr(instr: object, instr_registry: SelfIndexSet[object]) -> None:
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
            f"${DupElemError.OLD_ELEM_KEY}",
            old_instr,
            instr,
        )


def _add_rev_edges(graph: Graph) -> None:
    """Add reverse edges to the given graph.

    `graph` is the graph to add edges to.

    """
    edges = chain.from_iterable(
        ((name, pred.name) for pred in unit.predecessors if pred.name in graph)
        for name, unit in graph.nodes(_UNIT_KEY)
    )
    graph.add_edges_from(edges)


def _chk_unit_name(name: object, name_registry: SelfIndexSet[object]) -> None:
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
            f" ${DupElemError.OLD_ELEM_KEY}",
            old_name,
            name,
        )


def _chk_unit_width(unit: Mapping[object, Any]) -> None:
    """Check the given unit width.

    `unit` is the unit to load whose width.
    The function raises a BadWidthError if the width isn't positive.

    """
    if unit[UNIT_WIDTH_KEY] <= 0:
        raise BadWidthError(
            f"Functional unit ${BadWidthError.UNIT_KEY} has a bad width "
            f"${BadWidthError.WIDTH_KEY}.",
            *(map_ex([UNIT_NAME_KEY, UNIT_WIDTH_KEY], unit, gen=True)),
        )


def _create_graph(
    hw_units: Iterable[Mapping[object, object]],
    links: Iterable[Collection[str]],
) -> DiGraph:
    """Create a data flow graph for a processor.

    `hw_units` are the processor functional units.
    `links` are the connections between the functional units.
    The function returns a directed graph representing the reverse data
    flow through the processor functional units.

    """
    flow_graph = DiGraph()
    unit_registry = SelfIndexSet[object]()
    edge_registry = IndexedSet[Collection[str]](
        lambda edge: tuple(_get_edge_units(edge, unit_registry))
    )
    cap_registry = IndexedSet[_CapabilityInfo](Self.name())

    for cur_unit in hw_units:
        _add_unit(flow_graph, cur_unit, unit_registry, cap_registry)

    for cur_link in links:
        _add_edge(flow_graph, cur_link, unit_registry, edge_registry)

    return flow_graph


def _create_isa(
    isa_spec: Iterable[Tuple[str, str]], cap_registry: SelfIndexSet[object]
) -> Dict[str, object]:
    """Create an instruction set of the given ISA dictionary.

    `isa_spec` is the ISA specification to normalize.
    `cap_registry` is the store of supported capabilities.
    The function returns the ISA dictionary with upper-case instructions
    and standard capability names.

    """
    instr_registry = SelfIndexSet[object]()
    return {
        instr.upper(): _add_instr(
            instr_registry,
            cap_registry,
            *(ICaseString(prop) for prop in [instr, cap]),
        )
        for instr, cap in isa_spec
    }


def _get_acl_cap(
    unit: object, cap: str, global_cap_reg: IndexedSet[_CapabilityInfo]
) -> ICaseString:
    """Return a supported ACL capability name.

    `unit` is the unit to get a capability from whose memory ACL.
    `cap` is the capability to return whose standard form.
    `global_cap_reg` is the store of added capabilities across all
                     units.

    """
    std_cap = global_cap_reg.get(_CapabilityInfo(ICaseString(cap), unit))
    assert std_cap

    if std_cap.name.raw_str != cap:
        warning(
            f"Capability {cap} in unit {unit} memory ACL previously defined as"
            f" {std_cap.name} in unit {std_cap.unit}, using original "
            "definition..."
        )

    return std_cap.name


def _get_cap_name(
    capability: object, cap_registry: SelfIndexSet[object]
) -> object:
    """Return a supported capability name.

    `capability` is the name of the capability to validate.
    `cap_registry` is the store of supported capabilities.
    The function raises an UndefElemError if no capability with this
    name is supported, otherwise returns the supported capability name.

    """
    std_cap = cap_registry.get(capability)

    if not std_cap:
        raise UndefElemError(
            f"Unsupported capability ${UndefElemError.ELEM_KEY}", capability
        )

    return std_cap


def _get_edge_units(
    edge: Iterable[str], unit_registry: SelfIndexSet[object]
) -> "map[object]":
    """Return the units of an edge.

    `edge` is the edge to retrieve whose units.
    `unit_registry` is the store of units.

    """
    return maps(ICaseString, unit_registry.get, edge)


def _get_frozen_lst(obj_lst: Iterable[object]) -> Tuple[object, ...]:
    """Return a read-only list of the given objects.

    `obj_lst` is an iterable over the objects to be stored in the
              read-only list.

    """
    return tuple(obj_lst)


def _get_preds(
    processor: DiGraph, unit: object, unit_map: Mapping[object, _T]
) -> typing.Iterator[_T]:
    """Retrieve the predecessor units of the given unit.

    `processor` is the processor containing the unit.
    `unit` is the unit to retrieve whose predecessors.
    `unit_map` is the mapping between names and units.
    The function returns an iterator over predecessor units.

    """
    return map_ex(processor.predecessors(unit), unit_map, gen=True)


def _get_proc_units(graph: DiGraph) -> Generator[FuncUnit, None, None]:
    """Create units for the given processor graph.

    `graph` is the processor.
    The function returns an iterator over the processor functional
    units.

    """
    unit_map = {
        unit: _get_unit_entry(unit, graph.nodes[unit]) for unit in graph
    }
    return (
        FuncUnit(unit_map[name], _get_preds(graph, name, unit_map))
        for name in graph
    )


def _get_std_edge(
    edge: Iterable[str], unit_registry: SelfIndexSet[object]
) -> Generator[object, None, None]:
    """Return a validated edge.

    `edge` is the edge to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if an undefined unit is
    encountered.

    """
    return (_get_unit_name(ICaseString(unit), unit_registry) for unit in edge)


def _get_unit_entry(
    name: ICaseString, attrs: Mapping[object, Any]
) -> UnitModel:
    """Create a unit map entry from the given attributes.

    `name` is the unit name.
    `attrs` are the unit attribute dictionary.
    The function returns the unit model.

    """
    lock_attrs = map_ex([UNIT_RLOCK_KEY, UNIT_WLOCK_KEY], attrs, gen=True)
    return UnitModel(
        name,
        attrs[UNIT_WIDTH_KEY],
        attrs[UNIT_CAPS_KEY],
        units.LockInfo(*lock_attrs),
        attrs[UNIT_MEM_KEY],
    )


def _get_unit_graph(internal_units: Iterable[FuncUnit]) -> DiGraph:
    """Create a graph for internal units.

    `internal_units` are the internal units.

    """
    rev_graph = DiGraph()
    rev_graph.add_nodes_from(
        (unit.model.name, {_UNIT_KEY: unit}) for unit in internal_units
    )
    _add_rev_edges(rev_graph)
    return rev_graph


def _get_unit_name(
    unit: object, unit_registry: SelfIndexSet[object]
) -> object:
    """Return a validated unit name.

    `unit` is the name of the unit to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if no unit exists with this
    name, otherwise returns the validated unit name.

    """
    std_name = unit_registry.get(unit)

    if not std_name:
        raise UndefElemError(
            f"Undefined functional unit ${UndefElemError.ELEM_KEY}", unit
        )

    return std_name


def _init_cap_reg(capabilities: Iterable[object]) -> SelfIndexSet[object]:
    """Initialize a capability registry.

    `capabilities` are the unique capabilities to initially insert into
                   the registry.
    The function returns a capability registry containing the given
    unique capabilities.

    """
    cap_registry = SelfIndexSet[object]()

    for cap in capabilities:
        cap_registry.add(cap)

    return cap_registry


def _load_caps(
    unit: Mapping[object, Any], cap_registry: IndexedSet[_CapabilityInfo]
) -> List[object]:
    """Load the given unit capabilities.

    `unit` is the unit to load whose capabilities.
    `cap_registry` is the store of previously added capabilities.
    The function returns a list of loaded capabilities.

    """
    cap_list: List[object] = []
    unit_cap_reg = SelfIndexSet[object]()

    for cur_cap in unit[UNIT_CAPS_KEY]:
        _add_capability(
            unit[UNIT_NAME_KEY],
            ICaseString(cur_cap),
            cap_list,
            unit_cap_reg,
            cap_registry,
        )

    return cap_list


def _load_mem_acl(
    unit: Mapping[object, Any], cap_registry: IndexedSet[_CapabilityInfo]
) -> Generator[ICaseString, None, None]:
    """Load the given unit memory ACL.

    `unit` is the unit to load whose memory ACL.
    `cap_registry` is the store of valid capabilities.
    The function returns an iterator over loaded memory ACL
    capabilities.

    """
    return (
        _get_acl_cap(unit[UNIT_NAME_KEY], cap, cap_registry)
        for cap in unit.get(UNIT_MEM_KEY, [])
    )


def _post_order(internal_units: Iterable[FuncUnit]) -> Tuple[FuncUnit, ...]:
    """Create a post-order for internal units.

    `internal_units` are the internal units.
    The function uses a reverse graph to represent the internal units,
    thus a topological order of the reverse graph is a post-order for
    the normal graph. The function returns a tuple of the internal units
    in post-order.

    """
    rev_graph = _get_unit_graph(internal_units)
    return tuple(
        maps(
            rev_graph.nodes.get,
            operator.itemgetter(_UNIT_KEY),
            networkx.topological_sort(rev_graph),
        )
    )


def _prep_proc_desc(processor: DiGraph) -> None:
    """Prepare the given processor.

    `processor` is the processor to prepare.
    The function makes some preliminary checks against the processor and
    optimizes its structure by trying to only keep the effective units
    needed in a typical program execution. It raises an EmptyProcError
    if the processor doesn't contain any units, a NetworkXUnfeasible if
    the processor isn't a DAG, and a BlockedCapError if input width
    exceeds the minimum bus width.

    """
    _checks.chk_cycles(processor)
    port_info = _port_defs.PortGroup(processor)
    _optimization.clean_struct(processor)
    _optimization.rm_empty_units(processor)
    _optimization.chk_terminals(processor, port_info)
    _checks.chk_non_empty(processor, port_info.in_ports)
    _checks.chk_caps(processor)


def _sorted_units(hw_units: Iterable[object]) -> Tuple[FuncUnit, ...]:
    """Create a sorted list of the given units.

    `hw_units` are the units to create a sorted list of.

    """
    return container_utils.sorted_tuple(hw_units, key=Self.model.name())


@attr.s(frozen=True)
class ProcessorDesc:

    """Processor description"""

    in_ports: Tuple[UnitModel, ...] = attr.ib(converter=_get_frozen_lst)

    out_ports: Tuple[FuncUnit, ...] = attr.ib(converter=_sorted_units)

    in_out_ports: Tuple[UnitModel, ...] = attr.ib(converter=_get_frozen_lst)

    internal_units: Tuple[FuncUnit, ...] = attr.ib(converter=_post_order)


def get_abilities(processor: ProcessorDesc) -> typing.FrozenSet[object]:
    """Retrieve all capabilities supported by the given processor.

    `processor` is the processor to retrieve whose capabilities.

    """
    in_units = chain(processor.in_out_ports, processor.in_ports)
    return frozenset(
        chain.from_iterable(port.capabilities for port in in_units)
    )


def load_proc_desc(raw_desc: Mapping[object, Any]) -> ProcessorDesc:
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    proc_desc = _create_graph(raw_desc["units"], raw_desc["dataPath"])
    _prep_proc_desc(proc_desc)
    return _make_processor(proc_desc)


def _make_processor(proc_graph: DiGraph) -> ProcessorDesc:
    """Create a processor description from the given units.

    `proc_desc` is the processor graph.

    """
    unit_graph = _get_proc_units(proc_graph)
    in_out_ports = []
    in_ports = []
    internal_units = []
    out_ports = []

    for unit in unit_graph:
        match tuple(
            map(
                bool,
                [
                    proc_graph.in_degree(unit.model.name),
                    proc_graph.out_degree(unit.model.name),
                ],
            )
        ):
            case True, True:
                internal_units.append(unit)

            case True, False:
                out_ports.append(unit)

            case False, True:
                in_ports.append(unit.model)

            case _:
                in_out_ports.append(unit.model)

    return ProcessorDesc(in_ports, out_ports, in_out_ports, internal_units)


_add_src_path()
