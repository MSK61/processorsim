# -*- coding: utf-8 -*-

"""compiler services"""

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
# file:         program_utils.py
#
# function:     compilation services
#
# description:  loads and compiles programs
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

import errors
import itertools
import program_defs
import re


class CodeError(RuntimeError):

    """Syntax error"""

    # parameter indices in format message
    LINE_NUM_IDX = 0

    INSTR_IDX = 1

    def __init__(self, msg_tmpl, line, instr):
        """Create a syntax error.

        `self` is this syntax error.
        `msg_tmpl` is the error format message taking the line number as
                   a positional argument.
        `line` is the number of the line containing the error.
        `instr` is the instruction causing the error.

        """
        RuntimeError.__init__(self, msg_tmpl.format(line, instr))
        self._line = line
        self._instruction = instr

    @property
    def instruction(self):
        """Instruction where the error is encountered

        `self` is this syntax error.

        """
        return self._instruction

    @property
    def line(self):
        """Number of the source line containing the error

        `self` is this syntax error.

        """
        return self._line


class _LineInfo(object):

    """Source line information"""

    def __init__(self, instr, operands):
        """Set source line information.

        `self` is this source line information.
        `instr` is the instruction.
        `operands` are the instruction operands.

        """
        self._instruction = instr
        self._operands = operands

    @property
    def instruction(self):
        """Relevant instruction

        `self` is this source line information.

        """
        return self._instruction

    @property
    def operands(self):
        """Relevant instruction operands

        `self` is this source line information.

        """
        return self._operands


def compile_program(prog, isa):
    """Compile the program using the given instruction set.

    `prog` is the program to compile.
    `isa` is the instruction set.
    The function validates and translates the given program into a
    sequence that can be directly fed into a processor understanding the
    given instruction set and returns that sequence. The function raises an
    UndefElemError if an unsupported instruction is encountered.

    """
    return map(lambda progInstr: program_defs.HwInstruction(_get_cap(
        isa, progInstr), progInstr.sources, progInstr.destination), prog)


def read_program(prog_file):
    """Read the program stored in the given file.

    `prog_file` is the file containing the assembly program.
    The function returns the program instructions.

    """
    with open(prog_file) as program:

        program = itertools.imap(str.strip, program)
        return map(
            _create_instr, itertools.ifilter(
                lambda line_info: line_info[1], enumerate(program)))


def _get_cap(isa, instr):
    """Get the ISA capability of the given instruction.

    `isa` is the instruction set.
    `instr` is the program instruction to get whose capability.
    The function raises an UndefElemError if an unsupported instruction
    is encountered.

    """
    try:
        return isa[instr.name.upper()]
    except KeyError:  # unsupported instruction
        raise errors.UndefElemError(
            "Unsupported instruction {{}} at line {}".format(instr.line),
            instr.name)


def _get_line_parts(src_line_info):
    """Extract the source line components.

    `src_line_info` is the source line information.
    The function returns the structured line information. It raises a
    CodeError if there's a problem extracting components from the line.

    """
    sep = ' '
    line_parts = src_line_info[1].split(sep, 1)
    assert line_parts

    if len(line_parts) == 1:
        raise CodeError(
            "No operands provided for instruction {{{}}} at line "
            "{{{}}}".format(CodeError.INSTR_IDX, CodeError.LINE_NUM_IDX),
            src_line_info[0] + 1, line_parts[0])

    return _LineInfo(*line_parts)


def _get_operands(src_line_info, line_num):
    """Extract operands from the given line.

    `src_line_info` is the source line information.
    `line_num` is the line number in the original input.
    The function returns the relevant instruction operands as extracted
    from the line. It raises a CodeError if any of the operands is
    invalid.

    """
    sep_pat = "\s*,\s*"
    operands = re.split(sep_pat, src_line_info.operands)
    operand_indices = xrange(len(operands))
    try:
        raise CodeError(
            "Operand {} empty for instruction {{{}}} at line {{{}}}".format(
                itertools.ifilterfalse(
                    lambda operand_idx: operands[operand_idx],
                    operand_indices).next() + 1, CodeError.INSTR_IDX,
                CodeError.LINE_NUM_IDX), line_num, src_line_info.instruction)
    except StopIteration:  # all operands present
        return operands


def _create_instr(src_line_info):
    """Convert the source line to a program instruction.

    `src_line_info` is the program instruction line information.
    The function returns the created program instruction. It raises a
    CodeError if the instruction is malformed.

    """
    line_num = src_line_info[0] + 1
    src_line_info = _get_line_parts(src_line_info)
    operands = _get_operands(src_line_info, line_num)
    return program_defs.ProgInstruction(
        src_line_info.instruction, line_num, operands[1:], operands[0])
