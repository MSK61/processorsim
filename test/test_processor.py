#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor services"""

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
# file:         test_processor.py
#
# function:     processor service tests
#
# description:  tests processor and ISA loading
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

from itertools import imap, izip
import mock
import networkx
import os.path
import pytest
from pytest import mark, raises
import test_env
import processor_utils
from processor_utils import FuncUnit, UnitModel
import yaml

class TestEdge:

    """Test case for loading edges"""

    def test_edge_with_unknown_unit_raises_ElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        exChk = raises(
            processor_utils.ElemError, _read_file, "edgeWithUnknownUnit.yaml")
        assert exChk.value.element == "input"
        assert exChk.value.element in str(exChk.value)

    @mark.parametrize("in_file, bad_edge", [("emptyEdge.yaml", []),
        ("3UnitEdge.yaml", ["input", "middle", "output"])])
    def test_edge_with_wrong_number_of_units_raises_BadEdgeError(
        self, in_file, bad_edge):
        """Test loading an edge with wrong number of units.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_edge` is the bad edge.

        """
        exChk = raises(processor_utils.BadEdgeError, _read_file, in_file)
        assert exChk.value.edge == bad_edge
        assert str(bad_edge) in str(exChk.value)

    @mark.parametrize("in_file, edges",
                      [("twoEdgesWithSameUnitNamesAndCase.yaml",
                        [["input", "output"]]),
                        ("twoEdgesWithSameUnitNamesAndLowerThenUpperCase.yaml",
                         [["input", "output"], ["INPUT", "OUTPUT"]]),
                        ("twoEdgesWithSameUnitNamesAndUpperThenLowerCase.yaml",
                         [["INPUT", "OUTPUT"], ["input", "output"]])])
    def test_two_identical_edges_are_detected(self, in_file, edges):
        """Test loading two identical edges with the same units.

        `self` is this test case.
        `in_file` is the processor description file.
        `edges` are the identical edges.

        """
        with mock.patch("logging.warning") as warn_mock:
            _chk_two_units(_read_file(in_file))
        self._chk_edge_warn(edges, warn_mock)

    @staticmethod
    def _chk_edge_warn(edges, warn_mock):
        """Verify edges in a warning message.

        `edges` are the edges to assess.
        `warn_mock` is the warning function mock.
        The method asserts that all edges exist in the constructed warning
        message.

        """
        assert warn_mock.call_args
        warn_msg = warn_mock.call_args[0][0].format(
            *(warn_mock.call_args[0][1 :]), **(warn_mock.call_args[1]))
        assert all(imap(lambda edge: str(edge) in warn_msg, edges))


class TestLoop:

    """Test case for loading processors with loops"""

    @mark.parametrize("in_file", [
        "selfNodeProcessor.yaml", "bidirectionalEdgeProcessor.yaml",
        "bigLoopProcessor.yaml"])
    def test_loop_raises_NetworkXUnfeasible(self, in_file):
        """Test loading a processor with a loop.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        raises(networkx.NetworkXUnfeasible, _read_file, in_file)


class _UnitNode(object):

    """Functional unit node information"""

    def __init__(self, model, preds):
        """Set functional unit node information.

        `self` is this functional unit node.
        `model` is the unit model.
        `preds` are the predecessor nodes.

        """
        self._model = model
        self._preds = tuple(preds)

    @property
    def model(self):
        """Model of this functional unit node

        `self` is this functional unit node.

        """
        return self._model

    @property
    def predecessors(self):
        """Predecessor nodes for this functional unit node

        `self` is this functional unit node.

        """
        return self._preds


class TestUnits:

    """Test case for loading processor units"""

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = _read_file("4ConnectedUnitsProcessor.yaml")
        sorted_indices = sorted(
            xrange(len(proc_desc)), key=lambda idx: proc_desc[idx].model.name)
        exp_units = [_UnitNode(UnitModel("input", 1, []), []),
                     _UnitNode(UnitModel("middle", 1, []), ["input"]),
                     _UnitNode(UnitModel("output 1", 1, []), ["input"]),
                     _UnitNode(UnitModel("output 2", 1, []), ["middle"])]
        assert map(lambda idx: proc_desc[idx].model, sorted_indices) == \
        map(lambda unit: unit.model, exp_units)
        index_map = dict(imap(lambda entry: (entry[1].model.name, entry[0]),
                              enumerate(proc_desc)))
        chk_entries = izip(sorted_indices, exp_units)

        for cur_idx, cur_unit in chk_entries:
            self._assert_edges(
                proc_desc, cur_idx, cur_unit.predecessors, index_map)

    @mark.parametrize(
        "in_file", ["twoConnectedUnitsProcessor.yaml",
                    "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml"])
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        _chk_two_units(_read_file(in_file))

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        proc_desc = _read_file("singleUnitProcessor.yaml")
        assert len(proc_desc) == 1
        assert proc_desc[0].model == UnitModel("fullSys", 1, ["ALU"])
        assert not proc_desc[0].predecessors

    @mark.parametrize(
        "in_file, dup_unit", [("twoUnitsWithSameNameAndCase.yaml", "fullSys"),
            ("twoUnitsWithSameNameAndDifferentCase.yaml", "FULLsYS")])
    def test_two_units_with_same_name_raise_DupElemError(
        self, in_file, dup_unit):
        """Test loading two units with the same name.

        `self` is this test case.
        `in_file` is the processor description file.
        `dup_unit` is the duplicate unit.

        """
        exChk = raises(processor_utils.DupElemError, _read_file, in_file)
        elems = exChk.value.old_element, exChk.value.new_element
        assert elems == ("fullSys", dup_unit)
        assert all(imap(lambda elem: elem in str(exChk.value), elems))

    @classmethod
    def _assert_edges(cls, processor, unit_idx, predecessors, index_map):
        """Verify edges to predecessors of a unit.

        `cls` is this class.
        `processor` is the processor assess whose edges.
        `unit_idx` is the unit index.
        `predecessors` are the names of predecessor units.
        `index_map` is the mapping from unit names to indices.

        """
        assert len(processor[unit_idx].predecessors) == len(predecessors)
        pred_units = izip(sorted(processor[unit_idx].predecessors,
                                 key=lambda unit: unit.name), predecessors)

        for actual_pred, exp_pred in pred_units:
            cls._assert_pred(
                processor, actual_pred, index_map[exp_pred], unit_idx)

    @staticmethod
    def _assert_pred(processor, actual_pred, exp_pred, unit_idx):
        """Verify a predecessor.

        `processor` is the processor containing all units.
        `actual_pred` is the actual predecessor unit.
        `exp_pred` is the expected predecessor unit index.
        `unit_idx` is the unit index.

        """
        assert exp_pred > unit_idx
        assert actual_pred is processor[exp_pred].model

def main():
    """entry point for running test in this module"""
    pytest.main(__file__)


def _chk_two_units(processor):
    """Verify a two-unit processor.

    `processor` is the two-unit processor to assess.
    The function asserts the order and descriptions of units and links
    among them.

    """
    assert len(processor) == 2
    assert processor == [FuncUnit(UnitModel("output", 1, []), [
        processor[1].model]), FuncUnit(UnitModel("input", 1, []), [])]


def _read_file(file_name):
    """Read a processor description file.

    `file_name` is the processor description file name.

    """
    data_dir = "data"
    with open(os.path.join(data_dir, file_name)) as proc_file:
        return processor_utils.load_proc_desc(yaml.load(proc_file))


if __name__ == '__main__':
    main()
