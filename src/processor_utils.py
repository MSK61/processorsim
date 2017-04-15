# -*- coding: utf-8 -*-

"""low-level processor utilities"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# file:         processor_utils.py
#
# function:     low-level processor loading utilities
#
# description:  loads different entities inside a processor description
#               file
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

import itertools
from itertools import ifilterfalse, imap
import logging
import networkx
from networkx import DiGraph
import operator
from operator import itemgetter
# unit attributes
_UNIT_NAME_KEY = "name"
_UNIT_WIDTH_KEY = "width"

# exception types
class BadEdgeError(RuntimeError):

    """Bad edge error"""

    def __init__(self, msg_tmpl, edge):
        """Create a bad edge error.

        `self` is this bad edge error.
        `msg_tmpl` is the error format message taking the bad edge as a
                   positional argument.
        `edge` is the bad edge.

        """
        RuntimeError.__init__(self, msg_tmpl.format(edge))
        self._edge = edge

    @property
    def edge(self):
        """Bad edge

        `self` is this bad edge error.

        """
        return self._edge


class DupElemError(RuntimeError):

    """Duplicate set element error"""

    # parameter indices in format message
    OLD_ELEM_IDX = 0

    NEW_ELEM_IDX = 1

    def __init__(self, msg_tmpl, old_elem, new_elem):
        """Create a duplicate element error.

        `self` is this duplicate element error.
        `msg_tmpl` is the error format message taking in order the old
                   and new elements as positional parameters.
        `old_elem` is the element already existing.
        `new_elem` is the element just discovered.

        """
        RuntimeError.__init__(self, msg_tmpl.format(old_elem, new_elem))
        self._old_elem = old_elem
        self._new_elem = new_elem

    @property
    def new_element(self):
        """Duplicate element just discovered

        `self` is this duplicate element error.

        """
        return self._new_elem

    @property
    def old_element(self):
        """Element added before

        `self` is this duplicate element error.

        """
        return self._old_elem


class TightWidthError(RuntimeError):

    """Tight bus width error"""

    # parameter indices in format message
    REAL_WIDTH_IDX = 0

    MIN_WIDTH_IDX = 1

    def __init__(self, msg_tmpl, actual_width, min_width):
        """Create a tight bus width error.

        `self` is this width error.
        `msg_tmpl` is the error format message taking in order the
                   actual and minimum bus widths as positional
                   parameters.
        `actual_width` is the violating width value.
        `min_width` is the minimum allowed width.

        """
        RuntimeError.__init__(self, msg_tmpl.format(actual_width, min_width))
        self._actual_width = actual_width
        self._min_width = min_width

    @property
    def actual_width(self):
        """Violating width

        `self` is this tight bus width error.

        """
        return self._actual_width

    @property
    def min_width(self):
        """Minimum allowed width

        `self` is this tight bus width error.

        """
        return self._min_width


class UndefElemError(RuntimeError):

    """Unknown set element error"""

    def __init__(self, msg_tmpl, elem):
        """Create an unknown element error.

        `self` is this unknown element error.
        `msg_tmpl` is the error format message taking the unknown
                   element as a positional argument.
        `elem` is the unknown element.

        """
        RuntimeError.__init__(self, msg_tmpl.format(elem))
        self._elem = elem

    @property
    def element(self):
        """Unknown element

        `self` is this unknown element error.

        """
        return self._elem


class FuncUnit(object):

    """Processing functional unit"""

    def __init__(self, model, preds):
        """Create a functional unit.

        `self` is this functional unit.
        `model` is the unit model.
        `preds` is the list of units whose outputs are connected to the
                input of this unit.

        """
        self._model = model
        self._preds = tuple(preds)

    def __eq__(self, other):
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        return self._model == other.model and len(self._preds) == len(
            other.predecessors) and all(imap(
            operator.is_, sorted(self._preds), sorted(other.predecessors)))

    def __ne__(self, other):
        """Test if the two functional units are different.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        return not self == other

    @property
    def model(self):
        """Model of this functional unit

        `self` is this functional unit.

        """
        return self._model

    @property
    def predecessors(self):
        """Predecessor units of this functional unit

        `self` is this functional unit.

        """
        return self._preds


class ProcessorDesc(object):

    """Processor description"""

    def __init__(self, in_ports, out_ports, in_out_ports, internal_untis):
        """Create a processor.

        `self` is this processor.
        `in_ports` are the input-only ports.
        `out_ports` are the output-only ports.
        `in_out_ports` are the ports that act as both inputs and
                       outputs.
        `internal_untis` are the internal units that are neither exposed
                         as inputs or outputs.

        """
        self._in_ports = tuple(in_ports)
        self._out_ports = tuple(out_ports)
        self._in_out_ports = tuple(in_out_ports)
        self._internal_units = tuple(internal_untis)

    def __eq__(self, other):
        """Test if the two processors are identical.

        `self` is this processor.
        `other` is the other processor.

        """
        return self._in_ports == other.in_ports and \
                               self._out_ports == other.out_ports and \
                               self._in_out_ports == other.in_out_ports and \
                               self._internal_units == other.internal_units

    def __ne__(self, other):
        """Test if the two processors are different.

        `self` is this processor.
        `other` is the other processor.

        """
        return not self == other

    @property
    def in_out_ports(self):
        """Processor input-output ports

        `self` is this processor.

        """
        return self._in_out_ports

    @property
    def in_ports(self):
        """Processor input-only ports

        `self` is this processor.

        """
        return self._in_ports

    @property
    def internal_units(self):
        """Processor internal units

        `self` is this processor.
        An internal unit is a unit that's neither an input nor an
        output.

        """
        return self._internal_units

    @property
    def out_ports(self):
        """Processor output-only ports

        `self` is this processor.

        """
        return self._out_ports


class UnitModel(object):

    """Functional unit model"""

    def __init__(self, name, width, capabilities):
        """Create a functional unit model.

        `self` is this functional unit model.
        `name` is the unit model name.
        `width` is the unit model capacity.
        `capabilities` is the list of capabilities of instructions
                       supported by this unit model.

        """
        self._name = name
        self._width = width
        self._capabilities = frozenset(capabilities)

    def __eq__(self, other):
        """Test if the two functional unit models are identical.

        `self` is this functional unit model.
        `other` is the other functional unit model.

        """
        return self._name == other.name and self._width == other.width and \
                           self._capabilities == other.capabilities

    def __ne__(self, other):
        """Test if the two functional unit models are different.

        `self` is this functional unit model.
        `other` is the other functional unit model.

        """
        return not self == other

    def __hash__(self):
        """Calculate the hash of this functional unit model.

        `self` is this functional unit model.

        """
        return hash(self._name)

    @property
    def capabilities(self):
        """Unit model capabilities

        `self` is this functional unit model.

        """
        return self._capabilities

    @property
    def name(self):
        """Unit model name

        `self` is this functional unit model.

        """
        return self._name

    @property
    def width(self):
        """Unit model width

        `self` is this functional unit model.

        """
        return self._width


class _IndexedSet:

    """Indexed set"""

    def __init__(self, index_func):
        """Create an indexed set.

        `self` is this set.
        `index_func` is the index calculation function.

        """
        self._index_func = index_func
        self._std_form_map = {}

    def get(self, elem):
        """Retrieve the elem in this set matching the given one.

        `self` is this set.
        `elem` is the element to look up in this set.
        The method returns the element in this set that matches the
        given one, or None if none exists.

        """
        return self._std_form_map.get(self._index_func(elem))

    def add(self, elem):
        """Add the given element to this set.

        `self` is this set.
        `elem` is the element to add.

        """
        self._std_form_map[self._index_func(elem)] = elem


def load_proc_desc(raw_desc):
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    unit_sect = "units"
    data_path_sect = "dataPath"
    proc_desc = _create_graph(raw_desc[unit_sect], raw_desc[data_path_sect])
    _chk_proc_desc(proc_desc)
    name_caps = imap(_get_name_caps, raw_desc[unit_sect])
    return _make_processor(proc_desc, _post_order(proc_desc, dict(name_caps)))


def _get_anal_graph(processor):
    """Create a processor bus width analysis graph.

    `processor` is the processor to build an analysis graph from.

    """
    width_graph = DiGraph()
    units = enumerate(processor.nodes_iter())
    new_nodes = {}

    for idx, unit in units:
        _update_graph(idx, unit, processor, width_graph, new_nodes)

    width_graph.add_edges_from(imap(
        lambda edge: itemgetter(*edge)(new_nodes), processor.edges_iter()))
    return width_graph


def _get_name_caps(unit_desc):
    """Create an entry for a unit and its capabilities.

    `unit_desc` is the description to create a capability entry from.
    The function returns a tuple of the unit name and its capabilities.

    """
    unit_caps_key = "capabilities"
    return unit_desc[_UNIT_NAME_KEY], unit_desc[unit_caps_key]


def _get_port(degrees):
    """Find the port with respect to the given degrees.

    `degrees` are the degrees of all units.
    A port is a unit with zero degree.

    """
    return next(ifilterfalse(itemgetter(1), degrees))[0]


def _get_preds(processor, unit, unit_map):
    """Retrieve the predecessor units of the given unit.

    `processor` is the processor containing the unit.
    `unit` is the unit to retrieve whose predecessors.
    `unit_map` is mapping between names and units.
    The function returns an iterable of predecessor units.

    """
    return imap(lambda pred: unit_map[pred], processor.predecessors(unit))


def _get_std_edge(edge, unit_registry):
    """Return a validated edge.

    `edge` is the edge to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if an undefined unit is
    encountered.

    """
    return imap(lambda unit: _get_unit_name(unit, unit_registry), edge)


def _get_unit_entry(width, name, capabilities):
    """Create a unit map entry from the given attributes.

    `width` is the unit capacity.
    `name` is the unit name.
    `capabilities` are the unit capabilities.
    The function returns a tuple of the unit name and model.

    """
    return name, UnitModel(name, width, capabilities)


def _get_unit_name(unit, unit_registry):
    """Return a validated unit name.

    `unit` is the name of the unit to validate.
    `unit_registry` is the store of defined units.
    The function raises an UndefElemError if no unit exists with this
    name, otherwise returns the validated unit name.

    """
    std_name = unit_registry.get(unit)

    if std_name is None:
        raise UndefElemError("Undefined functional unit {}", unit)

    return std_name


def _set_capacities(graph, cap_edges):
    """Assign capacities to capping edges.

    `graph` is the graph containing edges.
    `cap_edges` are the capping edges.

    """
    cap_attr = "capacity"

    for cur_edge in cap_edges:
        graph[cur_edge[0]][cur_edge[1]][cap_attr] = min(
            imap(lambda unit: graph.node[unit][_UNIT_WIDTH_KEY], cur_edge))


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
        raise BadEdgeError(
            "Edge {} doesn't connect exactly 2 functional units.", edge)

    processor.add_edge(*(_get_std_edge(edge, unit_registry)))
    old_edge = edge_registry.get(edge)

    if old_edge is not None:
        logging.warning(
            "Edge {} previously added as {}, ignoring...", edge, old_edge)

    edge_registry.add(edge)


def _add_unit(processor, unit, unit_registry):
    """Add a functional unit to a processor.

    `processor` is the processor to add the unit to.
    `unit` is the functional unit to add.
    `unit_registry` is the store of previously added units.
    The function raises a DupElemError if a unit with the same name was
    previously added to the processor.

    """
    old_name = unit_registry.get(unit[_UNIT_NAME_KEY])

    if old_name is not None:
        raise DupElemError(
            "Functional unit {{{}}} previously added as {{{}}}".format(
                DupElemError.NEW_ELEM_IDX, DupElemError.OLD_ELEM_IDX),
            old_name, unit[_UNIT_NAME_KEY])

    processor.add_node(unit[_UNIT_NAME_KEY], width=unit[_UNIT_WIDTH_KEY])
    unit_registry.add(unit[_UNIT_NAME_KEY])


def _analyze_width(processor):
    """Analyze the processor bus width.

    `processor` is the processor to analyze whose width.

    """
    anal_graph = _get_anal_graph(processor)
    _aug_ports(anal_graph)
    _split_nodes(anal_graph)
    _dist_edge_caps(anal_graph)
    _chk_flow_vol(_min_width(anal_graph), _in_width(anal_graph))


def _aug_ports(graph):
    """Unify the ports in the graph.

    `graph` is the graph to weld whose ports.
    The function tries to connect several input and output ports into a
    single input port and a single output port.

    """
    for cur_terms in [[graph.in_degree_iter(), lambda *inputs: reversed(
        inputs)], [graph.out_degree_iter(), lambda *outputs: outputs]]:
        _aug_terminals(graph, *cur_terms)


def _aug_terminals(graph, degrees, edge_func):
    """Unify terminals indicated by degrees in the graph.

    `graph` is the graph containing terminals.
    `degrees` are the degrees of all units from the terminal side.
    `edge_func` is the creation function for edges connecting old
                terminals to the new one. It takes as parameters the old
                and the new terminals in order and returns the a tuple
                representing the directed edge between the two.
    The function tries to connect several terminals into a single new
    terminal.

    """
    ports = ifilterfalse(itemgetter(1), degrees)
    try:
        ports = itertools.chain([next(ports), next(ports)], ports)
    except StopIteration:  # single unit
        pass
    else:  # multiple units
        _unify_ports(graph, ports, edge_func)


def _chk_bus_width(processor):
    """Check the given processor bus width.

    `processor` is the processor to check.
    The function raises a TightWidthError if input width exceeds the
    minimum bus width.

    """
    if processor.number_of_nodes() > 1:
        _analyze_width(processor)


def _chk_cycles(processor):
    """Check the given processor for cycles.

    `processor` is the processor to check.
    The function raises a NetworkXUnfeasible if the processor isn't a
    DAG.

    """
    if not networkx.is_directed_acyclic_graph(processor):
        raise networkx.NetworkXUnfeasible()


def _chk_flow_vol(min_width, in_width):
    """Check the flow volume from the input throughout all units.

    `min_width` is the minimum bus width.
    `in_width` is the processor input width.
    The function raises a TightWidthError if the input width exceeds the
    minimum bus width.

    """
    if min_width < in_width:
        raise TightWidthError(
            "Input width {{{}}} exceeding minimum width {{{}}}".format(
                TightWidthError.REAL_WIDTH_IDX, TightWidthError.MIN_WIDTH_IDX),
            min_width, in_width)


def _chk_proc_desc(processor):
    """Check the given processor.

    `processor` is the processor to check.
    The function raises a NetworkXUnfeasible if the processor isn't a
    DAG and a TightWidthError if input width exceeds the minimum bus
    width.

    """
    for cur_chk in [_chk_cycles, _chk_bus_width]:
        cur_chk(processor)


def _coll_cap_edges(graph):
    """Collect capping edges from the given graph.

    `graph` is the graph to collect edges from.
    The function returns capping edges. A capping edge is the sole edge
    on either side of a node that determines the maximum flow through
    the node.

    """
    out_degrees = graph.out_degree()
    cap_edges = imap(lambda in_deg: next((graph.in_edges_iter if in_deg[1] ==
                                          1 else graph.out_edges_iter)(in_deg[
        0])), itertools.ifilter(lambda in_deg:
        in_deg[1] == 1 or out_degrees[in_deg[0]] == 1, graph.in_degree_iter()))
    return set(cap_edges)


def _create_graph(units, links):
    """Create a data flow graph for a processor.

    `units` is the processor functional units.
    `links` is the connections between the functional units.
    The function returns a directed graph representing the reverse data
    flow through the processor functional units.

    """
    flow_graph = DiGraph()
    unit_registry = _IndexedSet(str.lower)
    edge_registry = _IndexedSet(
        lambda edge: tuple(imap(unit_registry.get, edge)))

    for cur_unit in units:
        _add_unit(flow_graph, cur_unit, unit_registry)

    for cur_link in links:
        _add_edge(flow_graph, cur_link, unit_registry, edge_registry)

    return flow_graph


def _dist_edge_caps(graph):
    """Distribute capacities over edges as needed.

    `graph` is the graph containing edges.
    The function distributes capacities over capping edges.

    """
    _set_capacities(graph, _coll_cap_edges(graph))


def _in_port(graph):
    """Find the input port of the graph.

    `graph` is the graph to get whose input port.

    """
    return _get_port(graph.in_degree_iter())


def _in_width(graph):
    """Calculate the input capacity of the graph.

    `graph` is the graph to get whose input capacity.

    """
    return graph.node[_in_port(graph)][_UNIT_WIDTH_KEY]


def _min_width(processor):
    """Calculate the minimum bus width for the processor.

    `processor` is the processor to get whose minimum bus width.

    """
    return networkx.maximum_flow_value(
        processor, _in_port(processor), _out_port(processor))


def _out_port(graph):
    """Find the output port of the graph.

    `graph` is the graph to get whose output port.

    """
    return _get_port(graph.out_degree_iter())


def _post_order(graph, capabilities):
    """Create a post-order for the given processor.

    `graph` is the processor.
    `capabilities` are the capabilities of the functional units.
    The function returns a list of the processor functional units in
    post-order.

    """
    unit_map = dict(
        imap(lambda unit_entry: _get_unit_entry(graph.node[unit_entry[0]][
            _UNIT_WIDTH_KEY], *unit_entry), capabilities.iteritems()))
    return map(lambda name:
        FuncUnit(unit_map[name], _get_preds(graph, name, unit_map)),
        networkx.dfs_postorder_nodes(graph))


def _make_processor(proc_graph, post_ord):
    """Create a processor description from the given units.

    `proc_desc` is the processor graph.
    `post_ord` is the post-order of the processor units.

    """
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


def _split_node(graph, old_node, new_node):
    """Split a node into old and new ones.

    `graph` is the graph containing the node to be split.
    `old_node` is the existing node.
    `new_node` is the node added after splitting.

    """
    graph.add_node(new_node, width=graph.node[old_node][_UNIT_WIDTH_KEY])
    _mov_out_links(graph, graph.out_edges(old_node), new_node)
    graph.add_edge(old_node, new_node)


def _split_nodes(graph):
    """Split nodes in the given graph as necessary.

    `graph` is the graph containing nodes.
    The function splits nodes having multiple links on one side and a
    non-capping link on the other. A link on one side is capping if it's
    the only link on this side.

    """
    in_degrees = graph.in_degree_iter()
    out_degrees = graph.out_degree()
    ext_base = len(out_degrees)

    for unit, in_deg in in_degrees:
        if in_deg != 1 and out_degrees[unit] != 1 and (
            in_deg or out_degrees[unit]):
            _split_node(graph, unit, ext_base + unit)


def _add_port_link(graph, old_port, new_port, link):
    """Add a link between old and new ports.

    `graph` is the graph containing ports.
    `old_port` is the old port.
    `new_port` is the new port.
    `link` is the link connecting the two ports.

    """
    graph.node[new_port][_UNIT_WIDTH_KEY] += graph.node[old_port][
        _UNIT_WIDTH_KEY]
    graph.add_edge(*link)


def _unify_ports(graph, ports, edge_func):
    """Unify ports in the graph.

    `graph` is the graph containing terminals.
    `ports` are the ports to unify.
    `edge_func` is the creation function for edges connecting old
                terminals to the new one. It takes as parameters the old
                and the new terminals in order and returns the a tuple
                representing the directed edge between the two.

    """
    unified_port = graph.number_of_nodes()
    graph.add_node(unified_port, width=0)

    for cur_port in ports:
        _add_port_link(graph, cur_port[0], unified_port,
                       edge_func(cur_port[0], unified_port))


def _update_graph(idx, unit, processor, width_graph, unit_idx_map):
    """Update width graph structures.

    `idx` is the unit index.
    `unit` is the unit name.
    `processor` is the original processor.
    `width_graph` is the bus width analysis graph.
    `unit_idx_map` is the mapping between unit names and indices .

    """
    width_graph.add_node(idx, processor.node[unit])
    unit_idx_map[unit] = idx
