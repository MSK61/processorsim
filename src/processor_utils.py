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
from itertools import imap
import networkx
_UNIT_NAME_ATTR = "name"

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
        RuntimeError.__init__(self, msg_tmpl.format(new_elem, old_elem))
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


class _FuncUnit(object):

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


def load_proc_desc(raw_desc):
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    unit_sect = "units"
    data_path_sect = "dataPath"
    return _post_order(_create_graph(
        raw_desc[unit_sect], raw_desc[data_path_sect]), raw_desc[unit_sect])


def _get_preds(processor, unit, unit_map):
    """Retrieve the predecessor units of the given unit.

    `processor` is the processor containing the unit.
    `unit` is the unit to retrieve whose predecessors.
    `unit_map` is mapping between names and units.
    The function returns an iterable of predecessor units.

    """
    return imap(lambda pred: unit_map[pred], processor.predecessors(unit))


def _get_unit_entry(unit_desc):
    """Create a unit map entry from the given description.

    `unit_desc` is the description to create a unit map entry from.
    The function returns a tuple of the unit name and model.

    """
    return unit_desc[_UNIT_NAME_ATTR], UnitModel(*(imap(lambda attr:
        unit_desc[attr], [_UNIT_NAME_ATTR, "width", "capabilities"])))


def _add_unit(processor, unit, unit_registry):
    """Add a functional unit to a processor.

    `processor` is the processor to add the unit to.
    `unit` is the functional unit to add.
    `unit_registry` is the store of previously added units.
    The function raises a DupElemError if a unit with the same name was
    previously added to the processor.

    """
    lower_case_unit = unit.lower()
    first_name = unit_registry.get(lower_case_unit)

    if first_name is not None:
        raise DupElemError(
            "Functional unit {{{}}} previously added as {{{}}}".format(
                DupElemError.NEW_ELEM_IDX, DupElemError.OLD_ELEM_IDX),
            first_name, unit)

    processor.add_node(unit)
    unit_registry[lower_case_unit] = unit


def _create_graph(units, links):
    """Create a data flow graph for a processor.

    `units` is the processor functional units.
    `links` is the connections between the functional units.
    The function returns a directed graph representing the reverse data
    flow through the processor functional units.

    """
    flow_graph = networkx.DiGraph()
    unit_registry = {}

    for cur_unit in units:
        _add_unit(flow_graph, cur_unit[_UNIT_NAME_ATTR], unit_registry)

    flow_graph.add_edges_from(links)
    return flow_graph


def _post_order(graph, units):
    """Create a post-order for the given processor.

    `graph` is the processor.
    `units` is the processor functional units.
    The function returns a list of the processor functional units in
    post-order.

    """
    unit_map = dict(imap(_get_unit_entry, units))
    return map(
        lambda name: _FuncUnit(unit_map[name], _get_preds(
            graph, name, unit_map)), networkx.dfs_postorder_nodes(graph))
