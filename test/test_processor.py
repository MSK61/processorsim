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

import os.path
import src_importer
import processor_utils
from processor_utils import UnitModel
import pytest
import yaml

class _UnitNode:

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

    def test_processor_with_two_connected_functional_units(self):
        """Test loading a processor with two functional units.

        `self` is this test case.

        """
        in_file = "twoConnectedUnitsProcessor.yaml"
        proc_desc = self._read_file(in_file)
        assert [_UnitNode(UnitModel("output", 1, []), 1), _UnitNode(
            UnitModel("input", 1, []), 0)] == map(self._create_node, proc_desc)
        assert iter(proc_desc[0].predecessors).next() is proc_desc[1].model

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        in_file = "singleUnitProcessor.yaml"
        proc_desc = self._read_file(in_file)
        assert len(proc_desc) == 1
        assert proc_desc[0].model == UnitModel("fullSys", 1, ["ALU"])
        assert len(proc_desc[0].predecessors) == 0

    @pytest.mark.parametrize(
        "in_file, dup_unit", [("twoUnitsWithSameNameAndCase.yaml", "fullSys"),
            ("twoUnitsWithSameNameAndDifferentCase.yaml", "FULLsYS")])
    def test_two_units_with_same_name(self, in_file, dup_unit):
        """Test loading two units with the same name.

        `self` is this test case.
        `in_file` is the processor description file.
        `dup_unit` is the duplicate unit.

        """
        exChk = pytest.raises(
            processor_utils.DupElemError, self._read_file, in_file)
        assert exChk.value.old_element == "fullSys"
        assert exChk.value.new_element == dup_unit

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
