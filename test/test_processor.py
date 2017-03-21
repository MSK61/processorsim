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

from itertools import imap
import mock
import os.path
import pytest
from pytest import mark, raises
import test_env
import processor_utils
from processor_utils import UnitModel
import yaml

class _UnitNode(object):

    """Functional unit node information"""

    def __init__(self, model, preds):
        """Set functional unit node information.

        `self` is this functional unit node.
        `model` is the unit model.
        `preds` is the number of predecessor nodes.

        """
        self._model = model
        self._preds = preds

    def __eq__(self, other):
        """Test if the two functional unit nodes are identical.

        `self` is this functional unit node.
        `other` is the other functional unit node.

        """
        return self._model == other.model and self._preds == other.predecessors

    def __ne__(self, other):
        """Test if the two functional unit nodes are different.

        `self` is this functional unit node.
        `other` is the other functional unit node.

        """
        return not self == other

    @property
    def model(self):
        """Model of this functional unit node

        `self` is this functional unit node.

        """
        return self._model

    @property
    def predecessors(self):
        """Number of predecessor nodes for this functional unit node

        `self` is this functional unit node.

        """
        return self._preds


class TestProcDesc:

    """Test case for loading processor description"""

    def test_edge_with_unknown_unit_raises_ElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        exChk = raises(processor_utils.ElemError, self._read_file,
                       "edgeWithUnknownUnit.yaml")
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
        exChk = raises(processor_utils.BadEdgeError, self._read_file, in_file)
        assert exChk.value.edge == bad_edge
        assert str(bad_edge) in str(exChk.value)

    @mark.parametrize(
        "in_file", ["twoConnectedUnitsProcessor.yaml",
                    "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml"])
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        self._chk_two_units(self._read_file(in_file))

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        proc_desc = self._read_file("singleUnitProcessor.yaml")
        assert len(proc_desc) == 1
        assert proc_desc[0].model == UnitModel("fullSys", 1, ["ALU"])
        assert not proc_desc[0].predecessors

    @mark.parametrize(
        "in_file, edges",
        [("twoEdgesWithSameUnitNamesAndCase.yaml", [["input", "output"]]),
            ("twoEdgesWithSameUnitNamesAndLowerThenUpperCase.yaml",
             [["input", "output"], ["INPUT", "OUTPUT"]])])
    def test_two_identical_edges_are_detected(self, in_file, edges):
        """Test loading two identical edges with the same units.

        `self` is this test case.
        `in_file` is the processor description file.
        `edges` are the identical edges.

        """
        with mock.patch("logging.warning") as warn_mock:
            self._chk_two_units(self._read_file(in_file))
        self._chk_edge_warn(edges, warn_mock)

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
        exChk = raises(processor_utils.DupElemError, self._read_file, in_file)
        elems = exChk.value.old_element, exChk.value.new_element
        assert elems == ("fullSys", dup_unit)
        assert all(imap(lambda elem: elem in str(exChk.value), elems))

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

    @staticmethod
    def _chk_two_units(processor):
        """Verify a two-unit processor.

        `processor` is the two-unit processor to assess.
        The method asserts the order and descriptions of units and links
        among them.

        """
        assert [_UnitNode(UnitModel("output", 1, []), 1), _UnitNode(UnitModel(
            "input", 1, []), 0)] == map(TestProcDesc._create_node, processor)
        assert iter(processor[0].predecessors).next() is processor[1].model

    @staticmethod
    def _create_node(unit):
        """Create an information node for the given unit.

        `unit` is the unit to transform to a node.

        """
        return _UnitNode(unit.model, len(unit.predecessors))

    @staticmethod
    def _read_file(file_name):
        """Read a processor description file.

        `file_name` is the processor description file name.

        """
        data_dir = "data"
        with open(os.path.join(data_dir, file_name)) as proc_file:
            return processor_utils.load_proc_desc(yaml.load(proc_file))

def main():
    """entry point for running test in this module"""
    pytest.main(__file__)

if __name__ == '__main__':
    main()
