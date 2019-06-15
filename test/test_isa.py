#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests ISA loading service"""

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
# file:         test_isa.py
#
# function:     ISA loading service tests
#
# description:  tests ISA loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import pytest
from pytest import raises
from test_utils import chk_error, read_isa_file, ValInStrCheck
import errors
import processor_utils.exception
from str_utils import ICaseString


class TestIsa:

    """Test case for loading instruction sets"""

    def test_isa_with_unsupported_capabilitiy_raises_UndefElemError(self):
        """Test loading an instruction set with an unknown capability.

        `self` is this test case.

        """
        ex_chk = raises(errors.UndefElemError, read_isa_file,
                        "singleInstructionISA.yaml", [ICaseString("MEM")])
        chk_error([ValInStrCheck(ex_chk.value.element, ICaseString("ALU"))],
                  ex_chk.value)

    @pytest.mark.parametrize("in_file, supported_caps, exp_isa", [
        ("emptyISA.yaml", ["ALU"], {}),
        ("singleInstructionISA.yaml", ["ALU"], {"ADD": ICaseString("ALU")}),
        ("singleInstructionISA.yaml", ["alu"], {"ADD": ICaseString("alu")}),
        ("dualInstructionISA.yaml", ["ALU"],
         {"ADD": ICaseString("ALU"), "SUB": ICaseString("ALU")})])
    def test_load_isa(self, in_file, supported_caps, exp_isa):
        """Test loading an instruction set.

        `self` is this test case.
        `in_file` is the instruction set file.
        `supported_caps` are the supported hardware capabilities.
        `exp_isa` is the expected instruction set.

        """
        assert read_isa_file(
            in_file, map(ICaseString, supported_caps)) == exp_isa

    def test_two_instructions_with_same_name_raise_DupElemError(self):
        """Test loading two instructions with the same name.

        `self` is this test case.

        """
        ex_chk = raises(
            processor_utils.exception.DupElemError, read_isa_file,
            "twoInstructionsWithSameNameAndCase.yaml", [ICaseString("ALU")])
        chk_error([ValInStrCheck(ex_chk.value.new_element, ICaseString("add")),
                   ValInStrCheck(ex_chk.value.old_element,
                                 ICaseString("ADD"))], ex_chk.value)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
