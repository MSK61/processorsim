#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor optimization scenarios"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

from itertools import starmap
from logging import WARNING

import more_itertools
import pytest

import test_utils
from test_utils import chk_warnings, read_proc_file
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel


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
            "optimization", "pathThatGetsCutOffItsOutput.yaml"
        )
        wr_lock = LockInfo(False, True)
        assert proc_desc == ProcessorDesc(
            [UnitModel("input", 1, {"ALU": False}, LockInfo(True, False))],
            [
                FuncUnit(
                    UnitModel("output 1", 1, {"ALU": False}, wr_lock),
                    proc_desc.in_ports,
                )
            ],
            [],
            [],
        )
        chk_warnings(["middle"], caplog.records)

    def test_unit_with_empty_capabilities_is_removed(self, caplog):
        """Test loading a unit with no capabilities.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        assert read_proc_file(
            "optimization", "unitWithNoCapabilities.yaml"
        ) == ProcessorDesc(
            [],
            [],
            [UnitModel("core 1", 1, {"ALU": False}, LockInfo(True, True))],
            [],
        )
        chk_warnings(["core 2"], caplog.records)


class TestEdgeRemoval:
    """Test case for removing incompatible edges"""

    def test_incompatible_edge_is_removed(self, caplog):
        """Test an edge connecting two incompatible units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        proc_desc = read_proc_file(
            "optimization", "incompatibleEdgeProcessor.yaml"
        )
        in_units = starmap(
            lambda name, categ: UnitModel(
                name, 1, {categ: False}, LockInfo(True, False)
            ),
            [["input 1", "ALU"], ["input 2", "MEM"]],
        )
        wr_lock = LockInfo(False, True)
        out_units = starmap(
            lambda name, categ, in_unit: FuncUnit(
                UnitModel(name, 1, {categ: False}, wr_lock),
                [
                    more_itertools.first_true(
                        proc_desc.in_ports,
                        pred=lambda in_port: in_port.name == in_unit,
                    )
                ],
            ),
            [["output 1", "ALU", "input 1"], ["output 2", "MEM", "input 2"]],
        )
        assert proc_desc == ProcessorDesc(in_units, out_units, [], [])
        chk_warnings(["input 2", "output 1"], caplog.records)


class TestWidth:
    """Test case for checking data path width"""

    def test_output_more_capable_than_input(self):
        """Test an output which has more capabilities than the input.

        `self` is this test case.

        """
        test_utils.chk_two_units(
            "optimization", "oneCapabilityInputAndTwoCapabilitiesOutput.yaml"
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
