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
# function:     instruction sink classes
#
# description:  instruction sinks
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.47.2, python 3.8.3, Fedora release
#               32 (Thirty Two)
#
# notes:        This is a private program.
#
############################################################

import abc
from abc import abstractmethod
import itertools
import typing
from typing import Collection, Iterable, Iterator

import attr
import more_itertools

from container_utils import BagValDict
import processor_utils.units
import program_defs
from str_utils import ICaseString
from .sim_defs import InstrState, StallState
from . import _utils


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


class InstrSink(abc.ABC):

    """Instruction sink"""

    def fill_unit(self, util_info: BagValDict[ICaseString, InstrState],
                  mem_busy: bool) -> UnitFillStatus:
        """Fill this sink with instructions from its donors.

        `self` is this instruction sink.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.
        The method returns the sink filling status.

        """
        return self._fill(self._get_candidates(util_info), util_info, mem_busy)

    def _get_candidates(self, util_info: BagValDict[
            ICaseString, InstrState]) -> Collection[HostedInstr]:
        """Find candidate instructions in the donors of this sink.

        `self` is this instruction sink.
        `util_info` is the unit utilization information.

        """
        candidates = map(
            lambda pred: self._get_new_guests(pred, more_itertools.locate(
                util_info[pred], self._valid_candid)), self._donors)
        return self._pick_guests(
            itertools.chain.from_iterable(candidates), util_info)

    @staticmethod
    def _get_new_guests(src_unit: ICaseString,
                        instructions: Iterable[int]) -> Iterator[HostedInstr]:
        """Prepare new hosted instructions.

        `src_unit` is the old host of instructions.
        `instructions` are the new instructions to be hosted.

        """
        return map(lambda instr: HostedInstr(src_unit, instr), instructions)

    @abstractmethod
    def _accepts_cap(self, instr: int) -> bool:
        """Check if the given instruction capability may be accepted.

        `self` is this instruction sink.
        `instr` is the instruction to evaluate the acceptance of whose
                capability.

        """

    @abstractmethod
    def _fill(self, candidates: Collection[HostedInstr], util_info: BagValDict[
            ICaseString, InstrState], mem_busy: bool) -> UnitFillStatus:
        """Fill this sink.

        `self` is this instruction sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.

        """

    @abstractmethod
    def _pick_guests(
            self, candidates: Iterable[HostedInstr], util_info:
            BagValDict[ICaseString, InstrState]) -> Collection[HostedInstr]:
        """Pick the instructions to be accepted.

        `self` is this instruction sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.

        """

    def _valid_candid(self, instr: InstrState) -> bool:
        """Check if the given instruction is a good candidate.

        `self` is this instruction sink.
        `instr` is the instruction to evaluate whose acceptance chance.

        """
        return instr.stalled != StallState.DATA and self._accepts_cap(
            instr.instr)

    @abc.abstractproperty
    def _donors(self) -> Iterator[ICaseString]:
        """Retrieve the names of the units ready to supply instructions.

        `self` is this instruction sink.

        """


@attr.s(auto_attribs=True, frozen=True)
class OutSink(InstrSink):

    """Dummy sink for flushing output ports"""

    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    def _accepts_cap(self, instr: int) -> bool:
        """Always accept all instructions.

        `self` is this output sink.
        `instr` is unused.

        """
        return True

    def _fill(self, candidates: Collection[HostedInstr], util_info: BagValDict[
            ICaseString, InstrState], mem_busy: bool) -> UnitFillStatus:
        """Commit all candidate instructions to the output.

        `self` is this output sink.
        `candidates` are a list of candidate instructions.
        `util_info` is unused.
        `mem_busy` is unused.

        """
        return UnitFillStatus(candidates, False)

    def _pick_guests(
            self, candidates: Iterable[HostedInstr], util_info:
            BagValDict[ICaseString, InstrState]) -> Collection[HostedInstr]:
        """Pick all prospective instructions unconditionally.

        `self` is this output sink.
        `candidates` are a list of candidate instructions.
        `util_info` is unused.

        """
        return tuple(candidates)
    # pylint: enable=no-self-use
    # pylint: enable=unused-argument

    @property
    def _donors(self) -> Iterator[ICaseString]:
        """Retrieve the names of the output units.

        `self` is this output sink.

        """
        return self._out_ports

    _out_ports: Iterator[ICaseString]


@attr.s
class _InstrMovStatus:

    """Status of moving instructions"""

    moved: typing.List[HostedInstr] = attr.ib(factory=list, init=False)

    mem_used: bool = attr.ib(False, init=False)


@attr.s(auto_attribs=True, frozen=True)
class UnitSink(InstrSink):

    """Instruction sink wrapper for functional units"""

    def _accepts_cap(self, instr: int) -> bool:
        """Check if the given instruction capability may be accepted.

        `self` is this unit sink.
        `instr` is the instruction to evaluate the acceptance of whose
                capability.

        """
        return self._program[instr].categ in self._unit.model.capabilities

    def _fill(self, candidates: Collection[HostedInstr], util_info: BagValDict[
            ICaseString, InstrState], mem_busy: bool) -> UnitFillStatus:
        """Fill the underlying unit.

        `self` is this unit sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.

        """
        mov_res = self._mov_candidates(candidates, util_info, mem_busy)
        return UnitFillStatus(mov_res.moved, mov_res.mem_used)

    def _mov_candidate(self, candid_iter: Iterator[HostedInstr],
                       util_info: BagValDict[ICaseString, InstrState],
                       mem_busy: bool, mov_res: _InstrMovStatus) -> bool:
        """Move a candidate instruction between units.

        `self` is this unit sink.
        `candid_iter` is an iterator over the candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.
        `mov_res` is the move result to update the moved instructions
                  in.
        The method returns a flag indicating if moving instructions is still
        possible.

        """
        if _utils.unit_full(self._unit.model, util_info):
            return False

        try:
            candid = next(candid_iter)
        except StopIteration:
            return False
        mem_access = self._unit.model.needs_mem(self._program[
            util_info[candid.host][candid.index_in_host].instr].categ)

        if _utils.mem_unavail(mem_busy, mem_access):
            return True

        if mem_access:
            mov_res.mem_used = True

        util_info[candid.host][
            candid.index_in_host].stalled = StallState.NO_STALL
        util_info[self._unit.model.name].append(
            util_info[candid.host][candid.index_in_host])
        mov_res.moved.append(candid)
        return True

    def _mov_candidates(
            self, candidates: Collection[HostedInstr], util_info: BagValDict[
                ICaseString, InstrState], mem_busy: bool) -> _InstrMovStatus:
        """Move candidate instructions between units.

        `self` is this unit sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.

        """
        mov_res = _InstrMovStatus()
        candid_iter = iter(candidates)
        more_itertools.consume(iter(
            lambda: self._mov_candidate(candid_iter, util_info, mem_busy or
                                        mov_res.mem_used, mov_res), False))
        return mov_res

    def _pick_guests(
            self, candidates: Iterable[HostedInstr], util_info:
            BagValDict[ICaseString, InstrState]) -> Collection[HostedInstr]:
        """Pick the instructions to be accepted.

        `self` is this unit sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.

        """
        # Earlier instructions in the program are selected first.
        return sorted(candidates, key=lambda instr_info: util_info[
            instr_info.host][instr_info.index_in_host].instr)

    @property
    def _donors(self) -> Iterator[ICaseString]:
        """Retrieve the predecessor names.

        `self` is this unit sink.

        """
        return map(lambda pred: pred.name, self._unit.predecessors)

    _unit: processor_utils.units.FuncUnit

    _program: typing.Sequence[program_defs.HwInstruction]
