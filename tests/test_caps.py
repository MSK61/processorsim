#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading capabilities"""

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
# file:         test_caps.py
#
# function:     capability loading tests
#
# description:  tests loading capabilities
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

from logging import WARNING

from fastcore import basics
import pytest
from pytest import mark, raises

import test_utils
from test_utils import chk_warnings, read_proc_file
import processor_utils
from processor_utils import exception, units
from str_utils import ICaseString


class TestCaps:
    """Test case for loading capabilities"""

    # pylint: disable=invalid-name
    @mark.parametrize(
        "in_file",
        [
            "processorWithNoCapableInputs.yaml",
            "singleUnitWithNoCapabilities.yaml",
            "emptyProcessor.yaml",
        ],
    )
    def test_processor_with_incapable_ports_raises_EmptyProcError(
        self, in_file
    ):
        """Test a processor with no capable ports.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        with raises(exception.EmptyProcError) as ex_chk:
            read_proc_file("capabilities", in_file)
        assert "input" in ICaseString(str(ex_chk.value))

    @mark.parametrize(
        "in_file, bad_width",
        [
            ("singleUnitWithZeroWidth.yaml", 0),
            ("singleUnitWithNegativeWidth.yaml", -1),
        ],
    )
    def test_unit_with_non_positive_width_raises_BadWidthError(
        self, in_file, bad_width
    ):
        """Test loading a unit with a non-positive width.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_width` is the non-positive width.

        """
        with raises(exception.BadWidthError) as ex_chk:
            read_proc_file("capabilities", in_file)
        chk_points = (
            test_utils.ValInStrCheck(val_getter(ex_chk.value), exp_val)
            for val_getter, exp_val in [
                (basics.Self.unit(), "full system"),
                (basics.Self.width(), bad_width),
            ]
        )
        test_utils.chk_error(chk_points, ex_chk.value)


class TestDupCap:
    """Test case for loading duplicate capabilities"""

    def test_same_capability_with_different_cases_in_two_units_is_detected(
        self, caplog
    ):
        """Test loading a capability with different cases in two units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        in_file = "twoCapabilitiesWithSameNameAndDifferentCaseInTwoUnits.yaml"
        processor = (
            units.UnitModel(
                unit_name, 1, ["ALU"], units.LockInfo(True, True), []
            )
            for unit_name in ["core 1", "core 2"]
        )
        assert read_proc_file(
            "capabilities", in_file
        ) == processor_utils.ProcessorDesc([], [], processor, [])
        chk_warnings(["ALU", "core 1", "alu", "core 2"], caplog.records)
        assert ICaseString.__name__ not in caplog.records[0].getMessage()

    @mark.parametrize(
        "in_file, capabilities",
        [
            ("twoCapabilitiesWithSameNameAndCaseInOneUnit.yaml", ["ALU"]),
            (
                "twoCapabilitiesWithSameNameAndDifferentCaseInOneUnit.yaml",
                ["ALU", "alu"],
            ),
        ],
    )
    def test_two_capabilities_with_same_name_in_one_unit_are_detected(
        self, caplog, in_file, capabilities
    ):
        """Test loading two capabilities with the same name in one unit.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `in_file` is the processor description file.
        `capabilities` are the identical capabilities.

        """
        caplog.set_level(WARNING)
        test_utils.chk_one_unit("capabilities", in_file)
        chk_warnings(capabilities, caplog.records)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
