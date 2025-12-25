#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests ISA loading service"""

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
# file:         test_isa.py
#
# function:     ISA loading service tests
#
# description:  tests ISA loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.107.1, python 3.14.2, Fedora
#               release 43 (Forty Three)
#
# notes:        This is a private program.
#
############################################################

import logging

import pytest
import test_utils
from fastcore import basics
from pytest import raises
from test_utils import ValInStrCheck, chk_error, read_isa_file

import errors
import processor_utils
from str_utils import ICaseString


class TestDupInstr:
    """Test case for loading duplicate instructions"""

    def test_two_instructions_with_same_name_raise_DupElemError(self):
        """Test loading two instructions with the same name.

        `self` is this test case.

        """
        with raises(processor_utils.exception.DupElemError) as ex_chk:
            read_isa_file(
                "twoInstructionsWithSameNameAndCase.yaml", [ICaseString("ALU")]
            )
        chk_points = (
            ValInStrCheck(elem_getter(ex_chk.value), unit)
            for elem_getter, unit in [
                (basics.Self.new_element(), "add"),
                (basics.Self.old_element(), "ADD"),
            ]
        )
        chk_error(chk_points, ex_chk.value)


class TestIsa:
    """Test case for loading instruction sets"""

    def test_isa_with_capability_in_case_different_from_capabilities_list(
        self, caplog
    ):
        """Test loading an ISA with a capability in a different case.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(logging.WARNING)
        assert processor_utils.load_isa(
            [("ADD", "alu")], [ICaseString("ALU")]
        ) == {"ADD": "ALU"}
        test_utils.chk_warnings(["alu", "ALU"], caplog.records)

    def test_isa_with_unsupported_capabilitiy_raises_UndefElemError(self):
        """Test loading an instruction set with an unknown capability.

        `self` is this test case.

        """
        with raises(errors.UndefElemError) as ex_chk:
            read_isa_file("singleInstructionISA.yaml", [ICaseString("MEM")])
        chk_error([ValInStrCheck(ex_chk.value.element, "ALU")], ex_chk.value)

    @pytest.mark.parametrize(
        "in_file, supported_caps, exp_isa",
        [
            ("emptyISA.yaml", ["ALU"], {}),
            ("singleInstructionISA.yaml", ["ALU"], {"ADD": "ALU"}),
            ("singleInstructionISA.yaml", ["alu"], {"ADD": "alu"}),
            ("dualInstructionISA.yaml", ["ALU"], {"ADD": "ALU", "SUB": "ALU"}),
        ],
    )
    def test_load_isa(self, in_file, supported_caps, exp_isa):
        """Test loading an instruction set.

        `self` is this test case.
        `in_file` is the instruction set file.
        `supported_caps` are the supported hardware capabilities.
        `exp_isa` is the expected instruction set.

        """
        assert (
            read_isa_file(in_file, map(ICaseString, supported_caps)) == exp_isa
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
