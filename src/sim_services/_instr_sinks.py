# -*- coding: utf-8 -*-

"""instruction sinks"""

############################################################
#
# Copyright 2017, 2019, 2020 Mohammed El-Afifi
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
# file:         _instr_sinks.py
#
# function:     fill_unit
#
# description:  instruction sinks
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.47.0, python 3.8.3, Fedora release
#               32 (Thirty Two)
#
# notes:        This is a private program.
#
############################################################

import heapq
import itertools
import typing
from typing import Iterable, MutableSequence, Sequence

import attr
import more_itertools

from container_utils import BagValDict
from processor_utils.units import FuncUnit, UnitModel
from program_defs import HwInstruction
from str_utils import ICaseString
from .sim_defs import InstrState, StallState
_T = typing.TypeVar("_T")


def flush_outputs(out_units: Iterable[UnitModel],
                  util_info: BagValDict[ICaseString, InstrState]) -> None:
    """Flush output units in preparation for a new cycle.

    `out_units` are the output processing units.
    `util_info` is the unit utilization information.

    """
    for cur_out in out_units:
        _flush_output(util_info[cur_out.name])


def space_avail(
        unit: UnitModel, util_info: BagValDict[ICaseString, _T]) -> int:
    """Calculate the free space for receiving instructions in the unit.

    `unit` is the unit to test whose free space.
    `util_info` is the unit utilization information.

    """
    return unit.width - len(util_info[unit.name])


@attr.s(auto_attribs=True, frozen=True)
class HostedInstr:

    """Instruction hosted inside a functional unit"""

    host: ICaseString

    index_in_host: int


@attr.s(auto_attribs=True, frozen=True)
class UnitFillStatus:

    """Unit filling status"""

    instructions: Iterable[HostedInstr]

    mem_used: bool


@attr.s
class _InstrMovStatus:

    """Status of moving instructions"""

    moved: int = attr.ib(default=0, init=False)

    mem_used: bool = attr.ib(default=True, init=False)


def fill_unit(
        unit: FuncUnit, program: Sequence[HwInstruction], util_info:
        BagValDict[ICaseString, InstrState], mem_busy: bool) -> UnitFillStatus:
    """Fill an output with instructions from its predecessors.

    `unit` is the destination unit to fill.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.
    `mem_busy` is the memory busy flag.
    The function returns the destination unit filling status.

    """
    candidates = _get_candidates(unit, program, util_info)
    mov_res = _mov_candidates(
        candidates, unit.model, program, util_info, mem_busy)
    return UnitFillStatus(
        itertools.islice(candidates, mov_res.moved), mov_res.mem_used)


def _flush_output(out_instr_lst: MutableSequence[InstrState]) -> None:
    """Flush the output unit in preparation for a new cycle.

    `out_instr_lst` is the list of instructions in the output unit.

    """
    instr_indices = more_itertools.rlocate(
        out_instr_lst, lambda instr: instr.stalled == StallState.NO_STALL)

    for instr_index in instr_indices:
        del out_instr_lst[instr_index]


def _get_candidates(
        unit: FuncUnit, program: Sequence[HwInstruction], util_info:
        BagValDict[ICaseString, InstrState]) -> typing.List[HostedInstr]:
    """Find candidate instructions in the predecessors of a unit.

    `unit` is the unit to match instructions from predecessors against.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = (_get_new_guests(pred.name, more_itertools.locate(util_info[
        pred.name], lambda instr: instr.stalled != StallState.DATA and program[
            instr.instr].categ in unit.model.capabilities)) for pred in
                  unit.predecessors if pred.name in util_info)
    # Earlier instructions in the program are selected first.
    return heapq.nsmallest(
        space_avail(unit.model, util_info),
        itertools.chain.from_iterable(candidates), key=lambda instr_info:
        util_info[instr_info.host][instr_info.index_in_host].instr)


def _get_new_guests(src_unit: ICaseString, instructions:
                    Iterable[int]) -> typing.Iterator[HostedInstr]:
    """Prepare new hosted instructions.

    `src_unit` is the old host of instructions.
    `instructions` are the new instructions to be hosted.

    """
    return map(lambda instr: HostedInstr(src_unit, instr), instructions)


def _mov_candidate(
        candidate: InstrState, unit_util: MutableSequence[InstrState],
        mem_busy: bool, mem_access: bool, mov_res: _InstrMovStatus) -> bool:
    """Move a candidate instruction between units.

    `candidate` is the candidate instruction to move.
    `unit_util` is the unit utilization information.
    `mem_busy` is the memory busy flag.
    `mem_access` is the unit memory access flag.
    `mov_res` is the move result to update the number of moved
              instructions in.
    The function returns a flag indicating if the destination unit has
    received the instruction and held the memory busy.

    """
    if mem_busy and mem_access:
        return False

    candidate.stalled = StallState.NO_STALL
    unit_util.append(candidate)
    mov_res.moved += 1
    return mem_access


def _mov_candidates(
        candidates: typing.Collection[HostedInstr], unit: UnitModel,
        program: Sequence[HwInstruction], util_info: BagValDict[
            ICaseString, InstrState], mem_busy: bool) -> _InstrMovStatus:
    """Move candidate instructions between units.

    `candidates` are a list of tuples, where each tuple represents a
                 candidate instruction and its memory access requirement
                 in the destination unit.
    `unit` is the destination unit.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.
    `mem_busy` is the memory busy flag.

    """
    mov_res = _InstrMovStatus()

    for cur_candid in candidates:
        if _mov_candidate(
                util_info[cur_candid.host][cur_candid.index_in_host],
                util_info[unit.name], mem_busy,
                unit.needs_mem(program[util_info[cur_candid.host][
                    cur_candid.index_in_host].instr].categ), mov_res):
            return mov_res

    mov_res.mem_used = False
    return mov_res
