#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests compiler services"""

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
# file:         test_compiler.py
#
# function:     compiler service tests
#
# description:  tests program loading and compiling
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
import pytest
import test_utils
import exception
import program_defs
import program_utils
import unittest


class CoverageTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_HwInstruction_repr(self):
        """Test HwInstruction representation.

        `self` is this test case.

        """
        repr(program_defs.HwInstruction("ALU", [], "R1"))


class TestProgLoad:

    """Test case for loading programs"""

    @pytest.mark.parametrize("prog_file, isa, compiled_prog", [
        ("empty.asm", {}, []), ("singleInstruction.asm", {"ADD": "ALU"}, [
            program_defs.HwInstruction("ALU", ["R11", "R15"], "R14")])])
    def test_program(self, prog_file, isa, compiled_prog):
        """Test loading a program.

        `self` is this test case.

        """
        assert program_utils.compile(
            self._read_file(prog_file), isa) == compiled_prog

    def test_unsupported_instruction_raises_UndefElemError(self):
        """Test loading a program with an unknown instruction.

        `self` is this test case.

        """
        exChk = pytest.raises(
            exception.UndefElemError, program_utils.compile,
            self._read_file("subtractProgram.asm"), {"ADD": "ALU"})
        test_utils.chk_error([
            test_utils.ValInStrCheck(exChk.value.element, "SUB")], exChk.value)

    @staticmethod
    def _read_file(file_name):
        """Read a program file.

        `file_name` is the program file name.
        The function returns the loaded program.

        """
        test_dir = "programs"
        return program_utils.read_program(
            os.path.join(test_utils.TEST_DATA_DIR, test_dir, file_name))


def main():
    """entry point for running test in this module"""
    pytest.main(__file__)

if __name__ == '__main__':
    main()
