# -*- coding: utf-8 -*-

"""compiler services"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.85.1, python 3.11.6, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from collections.abc import Iterable, Mapping
import logging
from re import split
import string
import typing
from typing import Final

import attr
import fastcore.foundation

import container_utils
from container_utils import IndexedSet
from errors import UndefElemError
from program_defs import HwInstruction, ProgInstruction
from str_utils import ICaseString

_T = typing.TypeVar("_T")


class CodeError(RuntimeError):

    """Syntax error"""

    def __init__(self, msg_tmpl: str, line: object, instr: object) -> None:
        """Create a syntax error.

        `self` is this syntax error.
        `msg_tmpl` is the error message format taking the line number as
                   a positional argument.
        `line` is the number of the line containing the error.
        `instr` is the instruction causing the error.

        """
        super().__init__(
            string.Template(msg_tmpl).substitute(
                {self.INSTR_KEY: instr, self.LINE_NUM_KEY: line}
            )
        )
        self._line = line
        self._instr = instr

    @property
    def instr(self) -> object:
        """Instruction where the error is encountered

        `self` is this syntax error.

        """
        return self._instr

    @property
    def line(self) -> object:
        """Number of the source line containing the error

        `self` is this syntax error.

        """
        return self._line

    # parameter keys in message format
    INSTR_KEY: Final = "instruction"

    LINE_NUM_KEY: Final = "line"


def compile_program(
    prog: Iterable[ProgInstruction], isa: Mapping[str, object]
) -> list[HwInstruction]:
    """Compile the program using the given instruction set.

    `prog` is the program to compile.
    `isa` is the instruction set containing upper-case instructions.
    The function validates and translates the given program into a
    sequence that can be directly fed into a processor understanding the
    given instruction set and returns that sequence. The function raises an
    UndefElemError if an unsupported instruction is encountered.

    """
    return [
        HwInstruction(
            prog_instr.sources,
            prog_instr.destination,
            _get_cap(isa, prog_instr),
        )
        for prog_instr in prog
    ]


def read_program(prog_file: Iterable[str]) -> list[ProgInstruction]:
    """Read the program stored in the given file.

    `prog_file` is the file containing the assembly program.
    The function returns the program instructions.

    """
    prog = enumerate(map(str.strip, prog_file), 1)
    reg_registry = IndexedSet[_OperandInfo](fastcore.foundation.Self.name())
    return [
        _create_instr(line_no, line, reg_registry)
        for line_no, line in prog
        if line
    ]


@attr.frozen
class _LineInfo:

    """Source line information"""

    instruction: str

    operands: str


@attr.frozen
class _OperandInfo:

    """Instruction operand information"""

    name: ICaseString

    line: object


def _create_instr(
    line_num: object, line_txt: str, reg_registry: IndexedSet[_OperandInfo]
) -> ProgInstruction:
    """Convert the source line to a program instruction.

    `line_num` is the line number in the original input.
    `line_txt` is the line text.
    `reg_registry` is the register name registry.
    The function returns the created program instruction. It raises a
    CodeError if the instruction is malformed.

    """
    src_line_info = _get_line_parts(line_num, line_txt)
    dst, *sources = _get_operands(src_line_info, line_num, reg_registry)
    return ProgInstruction(sources, dst, src_line_info.instruction, line_num)


def _get_cap(isa: Mapping[str, _T], instr: ProgInstruction) -> _T:
    """Get the ISA capability of the given instruction.

    `isa` is the instruction set containing upper-case instructions.
    `instr` is the program instruction to get whose capability.
    The function raises an UndefElemError if an unsupported instruction
    is encountered.

    """
    try:
        return isa[instr.name.upper()]
    except KeyError as err:  # unsupported instruction
        raise UndefElemError(
            f"Unsupported instruction ${UndefElemError.ELEM_KEY} at line "
            f"{instr.line}",
            instr.name,
        ) from err


def _get_line_parts(line_num: object, line_txt: str) -> _LineInfo:
    """Extract the source line components.

    `line_num` is the line number in the original input.
    `line_txt` is the line text.
    The function returns the structured line information. It raises a
    CodeError if there's a problem extracting components from the line.

    """
    sep_pat = "\\s+"
    line_parts = split(sep_pat, line_txt, 1)
    assert line_parts

    if len(line_parts) == 1:
        raise CodeError(
            f"No operands provided for instruction ${CodeError.INSTR_KEY} at "
            f"line ${CodeError.LINE_NUM_KEY}",
            line_num,
            line_parts[0],
        )

    return _LineInfo(*line_parts)


def _get_operands(
    src_line_info: _LineInfo,
    line_num: object,
    reg_registry: IndexedSet[_OperandInfo],
) -> list[ICaseString]:
    """Extract operands from the given line.

    `src_line_info` is the source line information.
    `line_num` is the line number in the original input.
    `reg_registry` is the register name registry.
    The function returns the relevant instruction operands as extracted
    from the line. It raises a CodeError if any of the operands is
    invalid.

    """
    sep_pat = r"\s*,\s*"
    operands = enumerate(split(sep_pat, src_line_info.operands), 1)
    valid_ops = []

    for cur_op in operands:
        valid_ops.append(
            _get_reg_name(
                *cur_op, line_num, src_line_info.instruction, reg_registry
            )
        )

    return valid_ops


def _get_reg_name(
    op_idx: object,
    op_name: str,
    line_num: object,
    instr: object,
    reg_registry: IndexedSet[_OperandInfo],
) -> ICaseString:
    """Extract the registry name.

    `op_idx` is the one-based operand index.
    `op_name` is the operand name.
    `line_num` is the line number of the enclosing instruction.
    `instr` is the enclosing instruction.
    `reg_registry` is the register name registry.
    The function returns the register name. It raises a CodeError if the
    operand is invalid.

    """
    if not op_name:
        raise CodeError(
            f"Operand {op_idx} empty for instruction ${CodeError.INSTR_KEY} at"
            f" line ${CodeError.LINE_NUM_KEY}",
            line_num,
            instr,
        )

    std_reg = container_utils.get_from_set(
        reg_registry, _OperandInfo(ICaseString(op_name), line_num)
    )

    if std_reg.name.raw_str != op_name:
        logging.warning(
            "Register %s on line %d previously referred to as %s on line %d, "
            "using original reference...",
            op_name,
            line_num,
            std_reg.name,
            std_reg.line,
        )

    return std_reg.name
