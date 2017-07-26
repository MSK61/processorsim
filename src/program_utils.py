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
#
# notes:        This is a private program.
#
############################################################

import errors
import itertools
import program_defs


class SyntaxError(RuntimeError):

    """Syntax error"""

    def __init__(self, msg_tmpl, line):
        """Create a syntax error.

        `self` is this syntax error.
        `msg_tmpl` is the error format message taking the line number as
                   a positional argument.
        `line` is the number of the line containing the error.

        """
        RuntimeError.__init__(self, msg_tmpl.format(line))
        self._line = line

    @property
    def line(self):
        """Number of the source line containing the error

        `self` is this syntax error.

        """
        return self._line


def compile(prog, isa):
    """Compile the program using the given instruction set.

    `prog` is the program to compile.
    `isa` is the instruction set.
    The function validates and translates the given program into a
    sequence that can be directly fed into a processor understanding the
    given instruction set and returns that sequence. The function raises an
    UndefElemError if an unsupported instruction is encountered.

    """
    try:
        return map(lambda progInstr: program_defs.HwInstruction(
            isa[progInstr.name.upper()], progInstr.sources,
            progInstr.destination), prog)
    except KeyError as err:  # unsupported instruction
        raise errors.UndefElemError("Unsupported instruction {}", err.args[0])


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


def _create_instr(src_line_info):
    """Convert the source line to a program instruction.

    `src_line_info` is the program instruction line information.
    The function returns the created program instruction.

    """
    line_txt_idx = 1
    try:
        instr_name, operands = src_line_info[line_txt_idx].split()
    except ValueError:
        raise SyntaxError(
            "No operands provided for instruction {} at line {{}}".format(
                src_line_info[line_txt_idx]), src_line_info[0] + 1)
    operand_sep = ','
    operands = operands.split(operand_sep)
    return program_defs.ProgInstruction(instr_name, operands[1:], operands[0])
