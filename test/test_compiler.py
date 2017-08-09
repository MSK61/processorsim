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
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#
# notes:        This is a private program.
#
############################################################

import itertools
import os.path
import pytest
from pytest import mark, raises
import test_utils
from container_utils import contains
import errors
from program_defs import HwInstruction
import program_utils
from program_utils import CodeError, compile_program
from test_utils import ValInStrCheck
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
        `prog_file` is the program file.
        `isa` is the instruction set.
        `compiled_prog` is the compiled program.

        """
        assert compile_program(_read_file(prog_file), isa) == compiled_prog

    @mark.parametrize(
        "prog_file, instr, line_num",
        [("subtractProgram.asm", "SUB", 1), ("multiplyProgram.asm", "MUL", 2),
            ("lowerCaseSubtractProgram.asm", "sub", 1)])
    def test_unsupported_instruction_raises_UndefElemError(
            self, prog_file, instr, line_num):
        """Test loading a program with an unknown instruction.

        `self` is this test case.
        `prog_file` is the program file.
        `instr` is the unsupported instruction.
        `line_num` is the one-based number of the line containing the
                   unknown instruction missing operands.

        """
        ex_chk = raises(errors.UndefElemError, compile_program,
                        _read_file(prog_file), {"ADD": "ALU"})
        assert ex_chk.value.element == instr
        assert contains(str(ex_chk.value), [instr, str(line_num)])


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
        ex_chk = raises(CodeError, _read_file, prog_file)
        self._chk_syn_err(ex_chk.value, line_num, instr)
        assert str(operand) in str(ex_chk.value)

    @mark.parametrize("prog_file, line_num, instr",
                      [("firstInstructionWithNoOperands.asm", 1, "ADD"),
                       ("secondInstructionWithNoOperands.asm", 2, "SUB")])
    def test_instruction_with_no_operands_raises_SyntaxError(
            self, prog_file, line_num, instr):
        """Test loading an instruction with no operands.

        `self` is this test case.
        `prog_file` is the program file.
        `line_num` is the one-based number of the line containing the
                   instruction missing operands.
        `instr` is the instruction missing operands.

        """
        self._chk_syn_err(
            raises(CodeError, _read_file, prog_file).value, line_num, instr)

    @staticmethod
    def _chk_syn_err(syn_err, line_num, instr):
        """Check the properties of a syntax error.

        `syn_err` is the syntax error.
        `line_num` is the one-based number of the line containing the
                   syntax error.
        `instr` is the instruction with the syntax error.

        """
        test_utils.chk_error(itertools.imap(lambda err_params: ValInStrCheck(
            *err_params), [
            [syn_err.instruction, instr], [syn_err.line, line_num]]), syn_err)


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
