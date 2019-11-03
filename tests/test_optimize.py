#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor optimization scenarios"""

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
# file:         test_optimize.py
#
# function:     tests for processor optimization during loading
#
# description:  tests processor optimization
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.39.2, python 3.7.5, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

from logging import WARNING
import unittest

import test_utils
from test_utils import chk_warn, read_proc_file
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from str_utils import ICaseString


class TestClean:

    """Test case for cleaning(optimizing) a processor"""

    def test_data_path_cut_before_output_is_removed(self, caplog):
        """Test a data path that ends before reaching an output.

        `self` is this test case.
        `caplog` is the log capture fixture.
        Initially a data path never ends before reaching an output(since
        outputs in the first place are taken from where all paths end),
        however due to optimization operations a path may be cut before
        reaching its output so that a dead end may appear.

        """
        caplog.set_level(WARNING)
        proc_desc = read_proc_file(
            "optimization", "pathThatGetsCutOffItsOutput.yaml")
        out1_unit = ICaseString("output 1")
        alu_cap = ICaseString("ALU")
        assert proc_desc == ProcessorDesc([UnitModel(
            ICaseString("input"), 1, [alu_cap], LockInfo(True, False))], [
                FuncUnit(UnitModel(out1_unit, 1, [alu_cap], LockInfo(
                    False, True)), proc_desc.in_ports)], [], [])
        chk_warn(["middle"], caplog.records)

    def test_incompatible_edge_is_removed(self, caplog):
        """Test an edge connecting two incompatible units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        proc_desc = read_proc_file(
            "optimization", "incompatibleEdgeProcessor.yaml")
        # pylint: disable=not-an-iterable
        name_input_map = {
            in_port.name: in_port for in_port in proc_desc.in_ports}
        # pylint: enable=not-an-iterable
        alu_cap = ICaseString("ALU")
        mem_cap = ICaseString("MEM")
        out1_unit = ICaseString("output 1")
        out2_unit = ICaseString("output 2")
        assert proc_desc == ProcessorDesc(
            map(lambda unit_params: UnitModel(*unit_params),
                [[ICaseString("input 1"), 1, [alu_cap], LockInfo(True, False)],
                 [ICaseString("input 2"), 1, [mem_cap],
                  LockInfo(True, False)]]),
            map(lambda unit_params: FuncUnit(*unit_params),
                [[UnitModel(out1_unit, 1, [alu_cap], LockInfo(False, True)),
                  [name_input_map[ICaseString("input 1")]]],
                 [UnitModel(out2_unit, 1, [mem_cap], LockInfo(False, True)),
                  [name_input_map[ICaseString("input 2")]]]]), [], [])
        chk_warn(["input 2", "output 1"], caplog.records)

    def test_unit_with_empty_capabilities_is_removed(self, caplog):
        """Test loading a unit with no capabilities.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        assert read_proc_file(
            "optimization", "unitWithNoCapabilities.yaml") == ProcessorDesc(
                [], [], [UnitModel(ICaseString("core 1"), 1, [
                    ICaseString("ALU")], LockInfo(True, True))], [])
        chk_warn(["core 2"], caplog.records)


class WidthTest(unittest.TestCase):

    """Test case for checking data path width"""

    def test_output_more_capable_than_input(self):
        """Test an output which has more capabilities than the input.

        `self` is this test case.

        """
        test_utils.chk_two_units(
            "optimization", "oneCapabilityInputAndTwoCapabilitiesOutput.yaml")


def main():
    """entry point for running test in this module"""
    unittest.main()


if __name__ == '__main__':
    main()
