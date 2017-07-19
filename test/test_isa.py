#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests ISA loading service"""

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
# file:         test_isa.py
#
# function:     ISA loading service tests
#
# description:  tests ISA loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

import pytest
from pytest import raises
import test_utils
import errors
import processor_utils
from processor_utils import exception
from test_utils import chk_error, ValInStrCheck


class TestIsa:

    """Test case for loading instruction sets"""

    def test_isa_with_unsupported_capabilitiy_raises_UndefElemError(self):
        """Test loading an instruction set with an unknown capability.

        `self` is this test case.

        """
        exChk = raises(errors.UndefElemError, self._read_file,
                       "singleInstructionISA.yaml", ["MEM"])
        chk_error([ValInStrCheck(exChk.value.element, "ALU")], exChk.value)

    @pytest.mark.parametrize(
        "in_file, supported_caps, exp_isa", [("emptyISA.yaml", ["ALU"], {}), (
            "singleInstructionISA.yaml", ["ALU"], {"ADD": "ALU"}),
            ("singleInstructionISA.yaml", ["alu"], {"ADD": "alu"}), (
            "dualInstructionISA.yaml", ["ALU"], {"ADD": "ALU", "SUB": "ALU"})])
    def test_load_isa(self, in_file, supported_caps, exp_isa):
        """Test loading an instruction set.

        `self` is this test case.
        `in_file` is the instruction set file.
        `exp_isa` is the expected instruction set.

        """
        assert self._read_file(in_file, supported_caps) == exp_isa

    def test_two_instructions_with_same_name_raise_DupElemError(self):
        """Test loading two instructions with the same name.

        `self` is this test case.

        """
        exChk = raises(exception.DupElemError, self._read_file,
                       "twoInstructionsWithSameNameAndCase.yaml", ["ALU"])
        chk_error([ValInStrCheck(exChk.value.new_element, "add"),
                   ValInStrCheck(exChk.value.old_element, "ADD")], exChk.value)

    @staticmethod
    def _read_file(file_name, capabilities):
        """Read an instruction set file.

        `file_name` is the instruction set file name.
        `capabilities` are supported capabilities.
        The function returns the instruction set mapping.

        """
        test_dir = "ISA"
        return processor_utils.load_isa(
            test_utils.load_yaml(test_dir, file_name), capabilities)


def main():
    """entry point for running test in this module"""
    pytest.main(__file__)


if __name__ == '__main__':
    main()
