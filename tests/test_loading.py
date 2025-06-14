#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor loading service"""

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
# file:         test_loading.py
#
# function:     processor loading service tests
#
# description:  tests processor loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

import pytest
from pytest import mark

import test_utils
from test_utils import read_proc_file
import processor_utils
from processor_utils.units import FuncUnit, LockInfo, UnitModel


class TestProcessors:
    """Test case for loading valid processors"""

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = read_proc_file(
            "processors", "4ConnectedUnitsProcessor.yaml"
        )
        wr_lock = LockInfo(False, True)
        out_ports = tuple(
            FuncUnit(UnitModel(name, 1, ["ALU"], wr_lock, []), predecessors)
            for name, predecessors in [
                ("output 1", proc_desc.in_ports),
                (
                    "output 2",
                    (unit.model for unit in proc_desc.internal_units),
                ),
            ]
        )
        internal_unit = UnitModel(
            "middle", 1, ["ALU"], LockInfo(False, False), []
        )
        assert proc_desc == processor_utils.ProcessorDesc(
            [UnitModel("input", 1, ["ALU"], LockInfo(True, False), [])],
            out_ports,
            [],
            [FuncUnit(internal_unit, proc_desc.in_ports)],
        )

    @mark.parametrize(
        "in_file",
        [
            "twoConnectedUnitsProcessor.yaml",
            "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml",
        ],
    )
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        test_utils.chk_two_units("processors", in_file)

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        test_utils.chk_one_unit("processors", "singleALUProcessor.yaml")

    @mark.parametrize(
        "in_file",
        [
            "oneInputTwoOutputProcessor.yaml",
            "inputPortWithPartiallyConsumedCapability.yaml",
        ],
    )
    def test_valid_processor_raises_no_exceptions(self, in_file):
        """Test loading a valid processor raises no exceptions.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        read_proc_file("processors", in_file)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
