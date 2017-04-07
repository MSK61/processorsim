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


class ElemError(RuntimeError):

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
        self._preds = frozenset(preds)

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


class _WidthAnalyzer(object):

    """Processor bus width analyzer"""

    def __init__(self, processor, widths):
        """Create a processor bus width analyzer.

        `self` is this bus width analyzer.
        `processor` is the processor of the bus width analyzer.
        `widths` are the processor unit capacities.

        """
        self._width_graph = DiGraph()
        units = enumerate(processor.nodes_iter())
        new_nodes = {}

        for idx, unit in units:

            self._width_graph.add_node(idx, width=widths[unit])
            new_nodes[unit] = idx

        self._width_graph.add_edges_from(imap(
            lambda edge: itemgetter(*edge)(new_nodes), processor.edges_iter()))

    def aug_ports(self):
        """Unify the ports in the processor.

        `self` is this bus width analyzer.
        The method tries to connect several input and output ports into
        a single input port and a single output port.

        """
        for cur_terms in [[self._width_graph.in_degree_iter(),
                           lambda *inputs: reversed(inputs)],
            [self._width_graph.out_degree_iter(), lambda *outputs: outputs]]:
            self._aug_terminals(*cur_terms)

    def dist_capacities(self):
        """Distribute capacities over edges as needed.

        `self` is this bus width analyzer.
        The method distributes capacities over capping edges.

        """
        self._set_capacities(self._coll_cap_edges())

    def min_width(self):
        """Calculate the minimum bus width for the associated processor.

        `self` is this bus width analyzer.

        """
        in_port = self._get_port(self._width_graph.in_degree_iter())
        out_port = self._get_port(self._width_graph.out_degree_iter())
        return networkx.maximum_flow_value(
            self._width_graph, in_port[0], out_port[0])

    def split_nodes(self):
        """Split nodes as necessary.

        `self` is this bus width analyzer.
        The method splits nodes having multiple links on one side and a
        non-capping link on the other. A link on one side is capping if
        it's the only link on this side.

        """
        in_degrees = self._width_graph.in_degree_iter()
        out_degrees = self._width_graph.out_degree()
        ext_base = len(out_degrees)

        for unit, in_deg in in_degrees:
            if in_deg != 1 and out_degrees[unit] != 1 and (
                in_deg or out_degrees[unit]):

                source_node = ext_base + unit
                self._width_graph.add_node(
                    source_node,
                    width=self._width_graph.node[unit][_UNIT_WIDTH_KEY])
                out_links = self._width_graph.out_edges(unit)
                self._width_graph.add_edge(unit, source_node)

                # Move outgoing links to the new source node.
                for cur_link in out_links:

                    self._width_graph.add_edge(source_node, cur_link[1])
                    self._width_graph.remove_edge(*cur_link)

    @staticmethod
    def _get_port(degrees):
        """Find the port with respect to the given degrees.

        `degrees` are the degrees of all units.
        A port is a unit with zero degree.

        """
        return next(ifilterfalse(itemgetter(1), degrees))

    def _set_capacities(self, cap_edges):
        """Assign capacities to capping edges.

        `self` is this bus width analyzer.
        `cap_edges` are the capping edges.

        """
        cap_attr = "capacity"

        for cur_edge in cap_edges:
            self._width_graph[cur_edge[0]][cur_edge[1]][cap_attr] = min(
                imap(lambda unit:
                    self._width_graph.node[unit][_UNIT_WIDTH_KEY], cur_edge))

    def _aug_terminals(self, degrees, edge_func):
        """Unify terminals indicated by degrees in the processor.

        `self` is this bus width analyzer.
        `degrees` are the degrees of all units from the terminal side.
        `edge_func` is the creation function for edges connecting old
                    terminals to the new one. It takes as parameters the old
                    and the new terminals in order and returns the a tuple
                    representing the directed edge between the two.
        The method tries to connect several terminals into a single new
        terminal.

        """
        ports = ifilterfalse(itemgetter(1), degrees)
        try:
            ports = itertools.chain([next(ports), next(ports)], ports)
        except StopIteration:
            pass
        else:  # multiple units

            unified_port = self._width_graph.number_of_nodes()
            self._width_graph.add_node(unified_port, width=0)

            for cur_port in ports:

                self._width_graph.node[unified_port][
                    _UNIT_WIDTH_KEY] += self._width_graph.node[cur_port[0]][
                    _UNIT_WIDTH_KEY]
                self._width_graph.add_edge(
                    *(edge_func(cur_port[0], unified_port)))

    def _coll_cap_edges(self):
        """Collect capping edges.

        `self` is this bus width analyzer.
        The method returns capping edges. A capping edge is the sole
        edge on either side of a node that determines the maximum flow
        through the node.

        """
        out_degrees = self._width_graph.out_degree()
        cap_edges = imap(
            lambda in_deg: next((self._width_graph.in_edges_iter if in_deg[
                1] == 1 else self._width_graph.out_edges_iter)(in_deg[0])),
            itertools.ifilter(lambda in_deg: in_deg[1] == 1 or out_degrees[
                in_deg[0]] == 1, self._width_graph.in_degree_iter()))
        return set(cap_edges)

    @property
    def in_width(self):
        """Input capacity of the processor

        `self` is this bus width analyzer.

        """
        return self._width_graph.node[self._get_port(
            self._width_graph.in_degree_iter())[0]][_UNIT_WIDTH_KEY]


def load_proc_desc(raw_desc):
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    unit_sect = "units"
    data_path_sect = "dataPath"
    proc_desc = _create_graph(imap(itemgetter(_UNIT_NAME_KEY), raw_desc[
        unit_sect]), raw_desc[data_path_sect])
    _chk_proc_desc(proc_desc, dict(imap(_get_name_width, raw_desc[unit_sect])))
    return _post_order(proc_desc, raw_desc[unit_sect])


def _get_name_width(unit_desc):
    """Create a unit width entry from the given description.

    `unit_desc` is the description to create a unit width entry from.
    The function returns a tuple of the unit name and width.

    """
    return unit_desc[_UNIT_NAME_KEY], unit_desc[_UNIT_WIDTH_KEY]


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
    The function raises an ElemError if an undefined unit is
    encountered.

    """
    return imap(lambda unit: _get_unit_name(unit, unit_registry), edge)


def _get_unit_entry(unit_desc):
    """Create a unit map entry from the given description.

    `unit_desc` is the description to create a unit map entry from.
    The function returns a tuple of the unit name and model.

    """
    return unit_desc[_UNIT_NAME_KEY], UnitModel(
        *(itemgetter(_UNIT_NAME_KEY, _UNIT_WIDTH_KEY, "capabilities")(
            unit_desc)))


def _get_unit_name(unit, unit_registry):
    """Return a validated unit name.

    `unit` is the name of the unit to validate.
    `unit_registry` is the store of defined units.
    The function raises an ElemError if no unit exists with this name,
    otherwise returns the validated unit name.

    """
    std_name = unit_registry.get(unit)

    if std_name is None:
        raise ElemError("Undefined functional unit {}", unit)

    return std_name


def _add_edge(processor, edge, unit_registry, edge_registry):
    """Add an edge to a processor.

    `processor` is the processor to add the edge to.
    `edge` is the edge to add.
    `unit_registry` is the store of defined units.
    `edge_registry` is the store of previously added edges.
    The function raises a BadEdgeError if the edge doesn't connect
    exactly two units and an ElemError if an undefined unit is
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
    old_name = unit_registry.get(unit)

    if old_name is not None:
        raise DupElemError(
            "Functional unit {{{}}} previously added as {{{}}}".format(
                DupElemError.NEW_ELEM_IDX, DupElemError.OLD_ELEM_IDX),
            old_name, unit)

    processor.add_node(unit)
    unit_registry.add(unit)


def _chk_bus_width(processor, widths):
    """Check the given processor bus width.

    `processor` is the processor to check.
    `widths` are the processor unit capacities.
    The function raises a TightWidthError if input width exceeds the
    minimum bus width.

    """
    if processor.number_of_nodes() > 1:

        analyzer = _WidthAnalyzer(processor, widths)
        analyzer.aug_ports()
        analyzer.split_nodes()
        analyzer.dist_capacities()
        _chk_flow_vol(analyzer.min_width(), analyzer.in_width)


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


def _chk_proc_desc(processor, widths):
    """Check the given processor.

    `processor` is the processor to check.
    `widths` are the processor unit capacities.
    The function raises a NetworkXUnfeasible if the processor isn't a
    DAG and a TightWidthError if input width exceeds the minimum bus
    width.

    """
    _chk_cycles(processor)
    _chk_bus_width(processor, widths)


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


def _post_order(graph, units):
    """Create a post-order for the given processor.

    `graph` is the processor.
    `units` is the processor functional units.
    The function returns a list of the processor functional units in
    post-order.

    """
    unit_map = dict(imap(_get_unit_entry, units))
    return map(lambda name:
        FuncUnit(unit_map[name], _get_preds(graph, name, unit_map)),
        networkx.dfs_postorder_nodes(graph))
