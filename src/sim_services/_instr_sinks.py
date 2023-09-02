# -*- coding: utf-8 -*-

"""instruction sinks"""

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
# file:         _instr_sinks.py
#
# function:     instruction sink classes
#
# description:  instruction sinks
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

import abc
from abc import abstractmethod
import collections.abc
from collections.abc import Iterable, Iterator
import itertools
import typing

import attr
import fastcore.foundation
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


@attr.s
class InstrMovStatus:

    """Status of moving instructions"""

    moved: list[HostedInstr] = attr.ib(factory=list)

    mem_used: object = attr.ib(False, init=False)


class IInstrSink(abc.ABC):

    """Instruction sink"""

    def fill_unit(
        self, util_info: BagValDict[ICaseString, InstrState], mem_busy: object
    ) -> InstrMovStatus:
        """Fill this sink with instructions from its donors.

        `self` is this instruction sink.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.
        The method returns the sink filling status.

        """
        return self._fill(self._get_candidates(util_info), util_info, mem_busy)

    def _get_candidates(
        self, util_info: BagValDict[ICaseString, InstrState]
    ) -> Iterable[HostedInstr]:
        """Find candidate instructions in the donors of this sink.

        `self` is this instruction sink.
        `util_info` is the unit utilization information.

        """
        candidates = (
            self._get_new_guests(
                pred,
                more_itertools.locate(util_info[pred], self._valid_candid),
            )
            for pred in self._donors
        )
        return self._pick_guests(
            itertools.chain.from_iterable(candidates), util_info
        )

    @staticmethod
    def _get_new_guests(
        src_unit: ICaseString, instructions: Iterable[int]
    ) -> collections.abc.Generator[HostedInstr, None, None]:
        """Prepare new hosted instructions.

        `src_unit` is the old host of instructions.
        `instructions` are the new instructions to be hosted.

        """
        return (HostedInstr(src_unit, instr) for instr in instructions)

    @abstractmethod
    def _accepts_cap(self, instr: int) -> object:
        """Check if the given instruction capability may be accepted.

        `self` is this instruction sink.
        `instr` is the instruction to evaluate the acceptance of whose
                capability.

        """

    @abstractmethod
    def _fill(
        self,
        candidates: Iterable[HostedInstr],
        util_info: BagValDict[ICaseString, InstrState],
        mem_busy: object,
    ) -> InstrMovStatus:
        """Fill this sink.

        `self` is this instruction sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.

        """

    @abstractmethod
    def _pick_guests(
        self,
        candidates: Iterable[HostedInstr],
        util_info: BagValDict[ICaseString, InstrState],
    ) -> Iterable[HostedInstr]:
        """Pick the instructions to be accepted.

        `self` is this instruction sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.

        """

    def _valid_candid(self, instr: InstrState) -> object:
        """Check if the given instruction is a good candidate.

        `self` is this instruction sink.
        `instr` is the instruction to evaluate whose acceptance chance.

        """
        return instr.stalled != StallState.DATA and self._accepts_cap(
            instr.instr
        )

    @property
    @abstractmethod
    def _donors(self) -> Iterable[ICaseString]:
        """Retrieve the names of the units ready to supply instructions.

        `self` is this instruction sink.

        """


@attr.s(auto_attribs=True, frozen=True)
class OutSink(IInstrSink):

    """Dummy sink for flushing output ports"""

    def _accepts_cap(self, _: int) -> typing.Literal[True]:
        """Always accept all instructions.

        `self` is this output sink.
        `_` is unused.

        """
        return True

    def _fill(
        self,
        candidates: Iterable[HostedInstr],
        util_info: BagValDict[ICaseString, InstrState],
        mem_busy: object,
    ) -> InstrMovStatus:
        """Commit all candidate instructions to the output.

        `self` is this output sink.
        `candidates` are a list of candidate instructions.
        `util_info` is unused.
        `mem_busy` is unused.

        """
        return InstrMovStatus(list(candidates))

    def _pick_guests(
        self,
        candidates: Iterable[HostedInstr],
        _: BagValDict[ICaseString, InstrState],
    ) -> Iterable[HostedInstr]:
        """Pick all prospective instructions unconditionally.

        `self` is this output sink.
        `candidates` are a list of candidate instructions.
        `_` is unused.

        """
        return tuple(candidates)

    @property
    def _donors(self) -> Iterator[ICaseString]:
        """Retrieve the names of the output units.

        `self` is this output sink.

        """
        return self._out_ports

    _out_ports: Iterator[ICaseString]


@attr.s(auto_attribs=True, frozen=True)
class UnitSink(IInstrSink):

    """Instruction sink wrapper for functional units"""

    def _accepts_cap(self, instr: int) -> bool:
        """Check if the given instruction capability may be accepted.

        `self` is this unit sink.
        `instr` is the instruction to evaluate the acceptance of whose
                capability.

        """
        return self.program[instr].categ in self.unit.model.capabilities

    def _fill(
        self,
        candidates: Iterable[HostedInstr],
        util_info: BagValDict[ICaseString, InstrState],
        mem_busy: object,
    ) -> InstrMovStatus:
        """Move candidate instructions between units.

        `self` is this unit sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.
        `mem_busy` is the memory busy flag.

        """
        candid_iter = iter(candidates)
        mov_res = InstrMovStatus()
        more_itertools.consume(
            iter(
                lambda: _mov_candidate(
                    self,
                    candid_iter,
                    util_info,
                    mem_busy or mov_res.mem_used,
                    mov_res,
                ),
                False,
            )
        )
        return mov_res

    def _pick_guests(
        self,
        candidates: Iterable[HostedInstr],
        util_info: BagValDict[ICaseString, InstrState],
    ) -> Iterable[HostedInstr]:
        """Pick the instructions to be accepted.

        `self` is this unit sink.
        `candidates` are a list of candidate instructions.
        `util_info` is the unit utilization information.

        """
        # Earlier instructions in the program are selected first.
        return sorted(
            candidates,
            key=lambda instr_info: util_info[instr_info.host][
                instr_info.index_in_host
            ].instr,
        )

    @property
    def _donors(self) -> "map[ICaseString]":
        """Retrieve the predecessor names.

        `self` is this unit sink.

        """
        return map(fastcore.foundation.Self.name(), self.unit.predecessors)

    unit: processor_utils.units.FuncUnit

    program: collections.abc.Sequence[program_defs.HwInstruction]


def _mov_candidate(
    unit_sink: UnitSink,
    candid_iter: Iterator[HostedInstr],
    util_info: BagValDict[ICaseString, InstrState],
    mem_busy: object,
    mov_res: InstrMovStatus,
) -> bool:
    """Move a candidate instruction between units.

    `unit_sink` is the unit sink.
    `candid_iter` is an iterator over the candidate instructions.
    `util_info` is the unit utilization information.
    `mem_busy` is the memory busy flag.
    `mov_res` is the move result to update the moved instructions in.
    The method returns a flag indicating if moving instructions is still
    possible.

    """
    if _utils.unit_full(
        unit_sink.unit.model.width, util_info[unit_sink.unit.model.name]
    ):
        return False

    try:
        candid = next(candid_iter)
    except StopIteration:
        return False
    mem_access = unit_sink.unit.model.needs_mem(
        unit_sink.program[
            util_info[candid.host][candid.index_in_host].instr
        ].categ
    )

    if _utils.mem_unavail(mem_busy, mem_access):
        return True

    if mem_access:
        mov_res.mem_used = True

    util_info[candid.host][candid.index_in_host].stalled = StallState.NO_STALL
    util_info[unit_sink.unit.model.name].append(
        util_info[candid.host][candid.index_in_host]
    )
    mov_res.moved.append(candid)
    return True
