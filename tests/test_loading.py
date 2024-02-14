#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor loading service"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.86.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
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
from str_utils import ICaseString


class TestNoError:
    """Test case for no exceptions with valid processors"""

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


class TestProcessors:
    """Test case for loading valid processors"""

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = read_proc_file(
            "processors", "4ConnectedUnitsProcessor.yaml"
        )
        alu_cap = ICaseString("ALU")
        wr_lock = LockInfo(False, True)
        out_ports = tuple(
            FuncUnit(
                UnitModel(name, 1, [alu_cap], wr_lock, []).model2, predecessors
            )
            for name, predecessors in [
                (ICaseString("output 1"), _get_models2(proc_desc.in_ports)),
                (
                    ICaseString("output 2"),
                    (unit.model for unit in proc_desc.internal_units),
                ),
            ]
        )
        in_unit = ICaseString("input")
        internal_unit = UnitModel(
            ICaseString("middle"), 1, [alu_cap], LockInfo(False, False), []
        )
        assert proc_desc == processor_utils.ProcessorDesc(
            [
                UnitModel(
                    in_unit, 1, [alu_cap], LockInfo(True, False), []
                ).model2
            ],
            out_ports,
            [],
            [FuncUnit(internal_unit.model2, _get_models2(proc_desc.in_ports))],
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


def _get_models2(models):
    """Retrieve the UnitModel2 version of the given models.

    `models` are the UnitModel units to convert.

    """
    return models


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
