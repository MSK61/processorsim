#!/usr/bin/env python3
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
# environment:  Visual Studdio Code 1.38.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import unittest
from unittest import TestCase
from unittest.mock import patch

import test_utils
from test_utils import chk_warn, read_proc_file
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from str_utils import ICaseString


class CleanTest(TestCase):

    """Test case for cleaning(optimizing) a processor"""

    def test_data_path_cut_before_output_is_removed(self):
        """Test a data path that ends before reaching an output.

        `self` is this test case.
        Initially a data path never ends before reaching an output(since
        outputs in the first place are taken from where all paths end),
        however due to optimization operations a path may be cut before
        reaching its output so that a dead end may appear.

        """
        with patch("logging.warning") as warn_mock:
            proc_desc = read_proc_file(
                "optimization", "pathThatGetsCutOffItsOutput.yaml")
        out1_unit = ICaseString("output 1")
        alu_cap = ICaseString("ALU")
        lock_info = LockInfo(False, False)
        assert proc_desc == ProcessorDesc(
            [UnitModel(ICaseString("input"), 1, [alu_cap], lock_info)],
            [FuncUnit(UnitModel(out1_unit, 1, [alu_cap], lock_info),
                      proc_desc.in_ports)], [], [])
        chk_warn(["middle"], warn_mock.call_args)

    def test_incompatible_edge_is_removed(self):
        """Test an edge connecting two incompatible units.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            proc_desc = read_proc_file(
                "optimization", "incompatibleEdgeProcessor.yaml")
        # pylint: disable=not-an-iterable
        name_input_map = {
            in_port.name: in_port for in_port in proc_desc.in_ports}
        # pylint: enable=not-an-iterable
        alu_cap = ICaseString("ALU")
        lock_info = LockInfo(False, False)
        mem_cap = ICaseString("MEM")
        out1_unit = ICaseString("output 1")
        out2_unit = ICaseString("output 2")
        assert proc_desc == ProcessorDesc(
            map(lambda unit_params: UnitModel(*unit_params),
                [[ICaseString("input 1"), 1, [alu_cap], lock_info],
                 [ICaseString("input 2"), 1, [mem_cap], lock_info]]),
            map(lambda unit_params: FuncUnit(*unit_params),
                [[UnitModel(out1_unit, 1, [alu_cap], lock_info),
                  [name_input_map[ICaseString("input 1")]]],
                 [UnitModel(out2_unit, 1, [mem_cap], lock_info),
                  [name_input_map[ICaseString("input 2")]]]]), [], [])
        chk_warn(["input 2", "output 1"], warn_mock.call_args)

    def test_unit_with_empty_capabilities_is_removed(self):
        """Test loading a unit with no capabilities.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            assert read_proc_file(
                "optimization",
                "unitWithNoCapabilities.yaml") == ProcessorDesc(
                    [], [], [UnitModel(ICaseString("core 1"), 1, [
                        ICaseString("ALU")], LockInfo(False, False))], [])
        chk_warn(["core 2"], warn_mock.call_args)


class WidthTest(TestCase):

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
