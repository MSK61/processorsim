#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests compiler services"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.70.1, python 3.9.7, Fedora release
#               36 (Thirty Six)
#
# notes:        This is a private program.
#
############################################################

import itertools
from logging import WARNING

import pytest
from pytest import mark, raises

from . import test_utils
from .test_utils import read_prog_file
import errors
import program_defs
from program_defs import ProgInstruction
import program_utils
from program_utils import CodeError, read_program
from str_utils import ICaseString


class TestProgLoad:

    """Test case for loading programs"""

    @mark.parametrize(
        "prog_file, inputs", [("duplicateInputsInstruction.asm", ["R11"]),
                              ("lowerCaseInstruction.asm", ["R11", "R15"])])
    def test_program(self, prog_file, inputs):
        """Test loading a program.

        `self` is this test case.
        `prog_file` is the program file.
        `inputs` are the instruction inputs.

        """
        assert test_utils.compile_prog(prog_file, {
            "ADD": ICaseString("ALU")}) == [program_defs.HwInstruction(map(
                ICaseString, inputs), ICaseString("R14"), ICaseString("ALU"))]

    @mark.parametrize("dup_reg", ["R2", "R3"])
    def test_same_operand_with_different_case_in_same_instruction_is_detected(
            self, caplog, dup_reg):
        """Test loading operands in different cases(same instruction).

        `self` is this test case.
        `caplog` is the log capture fixture.
        `dup_reg` is the duplicate register.

        """
        lower_reg = dup_reg.lower()
        upper_reg = dup_reg.upper()
        caplog.set_level(WARNING)
        assert read_program([f"ADD R1, {upper_reg}, {lower_reg}"]) == [
            ProgInstruction(
                [ICaseString(dup_reg)], ICaseString("R1"), "ADD", 1)]
        assert caplog.records
        warn_msg = caplog.records[0].getMessage()

        for reg in [lower_reg, upper_reg]:
            assert reg in warn_msg

    @mark.parametrize("preamble", [0, 2])
    def test_same_operand_with_different_case_in_two_instructions_is_detected(
            self, caplog, preamble):
        """Test loading operands in different cases(two instructions).

        `self` is this test case.
        `caplog` is the log capture fixture.
        `preamble` is the number of lines preceding the instructions
                   containing registers.

        """
        caplog.set_level(WARNING)
        assert read_program(itertools.chain(itertools.repeat("", preamble), [
            "ADD R1, R2, R3", "ADD R4, r2, R5"])) == [
                ProgInstruction(map(ICaseString, in_regs), ICaseString(
                    out_reg), "ADD", line_no) for in_regs, out_reg, line_no in
                [(["R2", "R3"], "R1", preamble + 1),
                 (["r2", "R5"], "R4", preamble + 2)]]
        assert caplog.records
        warn_msg = caplog.records[0].getMessage()

        for reg in ["r2", str(preamble + 2), "R2", str(preamble + 1)]:
            assert reg in warn_msg

    # pylint: disable=invalid-name
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
                        read_prog_file(prog_file), {"ADD": ICaseString("ALU")})
        assert ex_chk.value.element == instr
        ex_chk = str(ex_chk.value)
        err_contents = [instr, str(line_num)]

        for part in err_contents:
            assert part in ex_chk


class TestSyntax:

    """Test case for syntax errors"""

    @mark.parametrize("prog_file", ["empty.asm", "emptyLineOnly.asm"])
    def test_empty_program(self, prog_file):
        """Test loading an empty program.

        `self` is this test case.
        `prog_file` is the program file.

        """
        self._test_program(prog_file, [])

    # pylint: disable=invalid-name
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
    # pylint: enable=invalid-name

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
    def test_well_formed_instruction(self, caplog, prog_file):
        """Test loading a single-instruction program.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `prog_file` is the program file.

        """
        caplog.set_level(WARNING)
        self._test_program(prog_file, [ProgInstruction(
            map(ICaseString, ["R11", "R15"]), ICaseString("R14"), "ADD", 1)])
        assert not caplog.records

    @staticmethod
    def _chk_syn_err(syn_err, line_num, instr):
        """Check the properties of a syntax error.

        `syn_err` is the syntax error.
        `line_num` is the one-based number of the line containing the
                   syntax error.
        `instr` is the instruction with the syntax error.

        """
        test_utils.chk_error(itertools.starmap(test_utils.ValInStrCheck, [
            [syn_err.instr, instr], [syn_err.line, line_num]]), syn_err)

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
