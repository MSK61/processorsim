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

import itertools
import os.path
import pytest
from pytest import mark, raises
import test_utils
import errors
from program_defs import HwInstruction
import program_utils
import unittest


class CoverageTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_HwInstruction_repr(self):
        """Test HwInstruction representation.

        `self` is this test case.

        """
        repr(HwInstruction("ALU", [], "R1"))


class TestProgLoad:

    """Test case for loading programs"""

    @mark.parametrize("prog_file, isa, compiled_prog", [
        ("empty.asm", {}, []), ("singleInstruction.asm", {"ADD": "ALU"},
                                [HwInstruction("ALU", ["R11", "R15"], "R14")]),
        ("lowerCaseSingleInstruction.asm", {"ADD": "ALU"}, [HwInstruction(
            "ALU", ["R11", "R15"], "R14")]), ("emptyLineOnly.asm", {}, [])])
    def test_program(self, prog_file, isa, compiled_prog):
        """Test loading a program.

        `self` is this test case.

        """
        assert program_utils.compile(
            _read_file(prog_file), isa) == compiled_prog

    def test_unsupported_instruction_raises_UndefElemError(self):
        """Test loading a program with an unknown instruction.

        `self` is this test case.

        """
        exChk = raises(errors.UndefElemError, program_utils.compile,
                       _read_file("subtractProgram.asm"), {"ADD": "ALU"})
        test_utils.chk_error([
            test_utils.ValInStrCheck(exChk.value.element, "SUB")], exChk.value)


class TestSyntax:

    """Test case for syntax errors"""

    @mark.parametrize("prog_file, line_num, instr, operand", [
        ("firstInstructionWithSecondOpernadEmpty.asm", 1, "ADD", 2),
        ("secondInstructionWithFirstOpernadEmpty.asm", 2, "SUB", 1)])
    def test_instruction_with_empty_operand_raises_SyntaxError(
            self, prog_file, line_num, instr, operand):
        """Test loading an instruction with an empty operand.

        `self` is this test case.
        `prog_file` is the program file.
        `line_num` is the one-based number of the line containing the
                   instruction with the empty operand.
        `instr` is the instruction with an empty operand.
        `operand` is the one-based index of the empty operand.

        """
        self._run_syn_err(prog_file, line_num, [instr, str(operand)])

    @mark.parametrize("prog_file, line_num, instr", [
        ("instructionAtFirstLineWithNoOperands.asm", 1, "ADD"),
        ("instructionAtSecondLineWithNoOperands.asm", 2, "SUB")])
    def test_instruction_with_no_operands_raises_SyntaxError(
            self, prog_file, line_num, instr):
        """Test loading an instruction with no operands.

        `self` is this test case.

        """
        self._run_syn_err(prog_file, line_num, [instr])

    @staticmethod
    def _run_syn_err(prog_file, line_num, err_details):
        """Test loading a program with a syntax error.

        `prog_file` is the program file.
        `line_num` is the one-based number of the line containing the
                   instruction with the empty operand.
        `err_details` are the syntax error details.

        """
        exChk = raises(program_utils.SyntaxError, _read_file, prog_file)
        assert exChk.value.line == line_num
        assert all(itertools.imap(lambda token: token in str(exChk.value),
                                  [str(line_num)] + err_details))


def main():
    """entry point for running test in this module"""
    pytest.main(__file__)


def _read_file(file_name):
    """Read a program file.

    `file_name` is the program file name.
    The function returns the loaded program.

    """
    test_dir = "programs"
    return program_utils.read_program(
        os.path.join(test_utils.TEST_DATA_DIR, test_dir, file_name))


if __name__ == '__main__':
    main()
