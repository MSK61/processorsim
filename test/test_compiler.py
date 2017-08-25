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
import pytest
from pytest import mark, raises
import test_utils
import container_utils
import errors
from program_defs import HwInstruction, Instruction, ProgInstruction
import program_utils
from program_utils import CodeError
from test_utils import read_prog_file
import unittest


class CoverageTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_HwInstruction_ne_operator(self):
        """Test HwInstruction != operator.

        `self` is this test case.

        """
        assert HwInstruction("ALU", [], "R1") != HwInstruction("ALU", [], "R2")

    def test_HwInstruction_repr(self):
        """Test HwInstruction representation.

        `self` is this test case.

        """
        repr(HwInstruction("ALU", [], "R1"))

    def test_Instruction_ne_operator(self):
        """Test Instruction != operator.

        `self` is this test case.

        """
        assert Instruction([], "R1") != Instruction([], "R2")

    def test_ProgInstruction_ne_operator(self):
        """Test ProgInstruction != operator.

        `self` is this test case.

        """
        assert ProgInstruction("ADD", 1, [], "R1") != ProgInstruction(
            "ADD", 2, [], "R1")

    def test_ProgInstruction_repr(self):
        """Test ProgInstruction representation.

        `self` is this test case.

        """
        repr(ProgInstruction("ADD", 1, ["R1"], "R1"))


class TestProgLoad:

    """Test case for loading programs"""

    def test_duplicate_inputs_are_stored_only_once(self):
        """Test loading a program with duplicate inputs.

        `self` is this test case.
        The functions tests loading a program where one instruction takes both
        inputs from the same register.

        """
        self._test_program("duplicateInputsInstruction.asm", ["R11"])

    def test_lower_case_instruction(self):
        """Test loading a lower case instruction.

        `self` is this test case.

        """
        self._test_program("lowerCaseInstruction.asm", ["R11", "R15"])

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
        ex_chk = raises(errors.UndefElemError, program_utils.compile_program,
                        read_prog_file(prog_file), {"ADD": "ALU"})
        assert ex_chk.value.element == instr
        assert container_utils.contains(
            str(ex_chk.value), [instr, str(line_num)])

    @staticmethod
    def _test_program(prog_file, inputs):
        """Test loading a program.

        `prog_file` is the program file.
        `inputs` are the instruction inputs.

        """
        assert test_utils.compile_prog(prog_file, {"ADD": "ALU"}) == [
            HwInstruction("ALU", inputs, "R14")]


class TestSyntax:

    """Test case for syntax errors"""

    @mark.parametrize("prog_file", ["empty.asm", "emptyLineOnly.asm"])
    def test_empty_program(self, prog_file):
        """Test loading an empty program.

        `self` is this test case.
        `prog_file` is the program file.

        """
        self._test_program(prog_file, [])

    @mark.parametrize("prog_file, line_num, instr, operand", [
        ("firstInstructionWithSecondOpernadEmpty.asm", 1, "ADD", 2),
        ("secondInstructionWithFirstOpernadEmpty.asm", 2, "SUB", 1)])
    def test_instruction_with_empty_operand_raises_CodeError(
            self, prog_file, line_num, instr, operand):
        """Test loading an instruction with an empty operand.

        `self` is this test case.
        `prog_file` is the program file.
        `line_num` is the one-based number of the line containing the
                   instruction with the empty operand.
        `instr` is the instruction with an empty operand.
        `operand` is the one-based index of the empty operand.

        """
        ex_chk = raises(CodeError, read_prog_file, prog_file)
        self._chk_syn_err(ex_chk.value, line_num, instr)
        assert str(operand) in str(ex_chk.value)

    @mark.parametrize("prog_file, line_num, instr",
                      [("firstInstructionWithNoOperands.asm", 1, "ADD"),
                       ("secondInstructionWithNoOperands.asm", 2, "SUB")])
    def test_instruction_with_no_operands_raises_CodeError(
            self, prog_file, line_num, instr):
        """Test loading an instruction with no operands.

        `self` is this test case.
        `prog_file` is the program file.
        `line_num` is the one-based number of the line containing the
                   instruction missing operands.
        `instr` is the instruction missing operands.

        """
        self._chk_syn_err(raises(CodeError, read_prog_file, prog_file).value,
                          line_num, instr)

    @mark.parametrize("prog_file", [
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "instructionWithOneSpaceBeforeComma.asm",
        "instructionWithOneSpaceAfterComma.asm",
        "instructionWithTwoSpacesBeforeComma.asm",
        "instructionWithTwoSpacesAfterComma.asm",
        "instructionWithOneTabBeforeComma.asm",
        "instructionWithOneTabAfterComma.asm",
        "instructionWithTwoSpacesBeforeOperands.asm",
        "instructionWithOneTabBeforeOperands.asm"])
    def test_well_formed_instruction(self, prog_file):
        """Test loading a single-instruction program.

        `self` is this test case.
        `prog_file` is the program file.

        """
        self._test_program(
            prog_file, [ProgInstruction("ADD", 1, ["R11", "R15"], "R14")])

    @staticmethod
    def _chk_syn_err(syn_err, line_num, instr):
        """Check the properties of a syntax error.

        `syn_err` is the syntax error.
        `line_num` is the one-based number of the line containing the
                   syntax error.
        `instr` is the instruction with the syntax error.

        """
        test_utils.chk_error(
            itertools.imap(
                lambda err_params: test_utils.ValInStrCheck(*err_params),
                [[syn_err.instruction, instr], [syn_err.line, line_num]]),
            syn_err)

    @staticmethod
    def _test_program(prog_file, loaded_prog):
        """Test loading a program.

        `prog_file` is the program file.
        `loaded_prog` is the loaded program.

        """
        assert read_prog_file(prog_file) == loaded_prog


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
