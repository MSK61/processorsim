# -*- coding: utf-8 -*-

"""simulation services"""

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
# file:         sim_services.py
#
# function:     program execution simulation services
#
# description:  simulates program execution
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.41.1, python 3.7.6, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import collections
import copy
import enum
from enum import auto
import heapq
from itertools import chain
import operator
import string
import typing
from typing import Dict, Iterable, Iterator, List, Mapping, MutableSequence, \
    Sequence, Tuple

import attr

import container_utils
from container_utils import BagValDict
from processor_utils import ProcessorDesc
import processor_utils.units
from processor_utils.units import FuncUnit, UnitModel
from program_defs import HwInstruction
from reg_access import AccessType, RegAccessQueue, RegAccQBuilder
from str_utils import ICaseString
_T = typing.TypeVar("_T")


class StallError(RuntimeError):

    """Stalled processor error"""

    def __init__(self, msg_tmpl: str, fed_commands: object) -> None:
        """Create a stalled processor error.

        `self` is this stalled processor error.
        `msg_tmpl` is the error message format taking the stalled
                   processor state as a positional argument.
        `fed_commands` is the number of instructions fed to the
                       processor so far.

        """
        # Casting dictionary values since the type hint in typeshed for
        # Template.substitute unnecessarily stipulates string values.
        RuntimeError.__init__(self, string.Template(msg_tmpl).substitute(
            {self.STATE_KEY: typing.cast(str, fed_commands)}))
        self._fed_commands = fed_commands

    @property
    def fed_commands(self) -> object:
        """Stalled processor state

        `self` is this stalled processor error.

        """
        return self._fed_commands

    STATE_KEY = "state"  # parameter key in message format


@attr.s(frozen=True)
class HwSpec:

    """Hardware specification"""

    processor_desc: ProcessorDesc = attr.ib()

    name_unit_map: Dict[ICaseString, UnitModel] = attr.ib(init=False)

    @name_unit_map.default
    def _build_unit_map(self) -> Dict[ICaseString, UnitModel]:
        """Build the name-to-unit mapping.

        `self` is this hardware specification.

        """
        # pylint: disable=no-member
        models = chain(
            self.processor_desc.in_ports, self.processor_desc.in_out_ports,
            map(lambda func_unit: func_unit.model,
                chain(self.processor_desc.out_ports,
                      self.processor_desc.internal_units)))
        return {unit.name: unit for unit in models}


class StallState(enum.Enum):

    """Instruction stalling state"""

    NO_STALL = auto()

    STRUCTURAL = auto()

    DATA = auto()


@attr.s
class InstrState:

    """Instruction state"""

    instr: int = attr.ib()

    stalled: StallState = attr.ib(
        default=StallState.NO_STALL,
        validator=attr.validators.instance_of(StallState))


def simulate(program: Sequence[HwInstruction], hw_info: HwSpec) -> List[
        BagValDict[ICaseString, InstrState]]:
    """Run the given program on the processor.

    `program` is the program to run.
    `hw_info` is the processor information.
    The function returns the pipeline diagram.

    """
    util_tbl: List[BagValDict[ICaseString, InstrState]] = []
    acc_queues = _build_acc_plan(enumerate(program))
    issue_rec = _IssueInfo()
    prog_len = len(program)

    while issue_rec.entered < prog_len or issue_rec.in_flight:
        _run_cycle(program, acc_queues, hw_info, util_tbl, issue_rec)

    return util_tbl


@attr.s(auto_attribs=True, frozen=True)
class _HostedInstr:

    """Instruction hosted inside a functional unit"""

    host: ICaseString

    index_in_host: int


class _IssueInfo:

    """Instruction issue information record"""

    def __init__(self) -> None:
        """Create an issue information record.

        `self` is this issue information record.

        """
        self._entered = 0
        self._exited = 0

    def bump_input(self) -> None:
        """Increment the entered instructions index.

        `self` is this issue information record.

        """
        self._entered += 1

    def pump_outputs(self, outputs: int) -> None:
        """Pump outputs out of the pipeline.

        `self` is this issue information record.
        `outputs` is the number of outputs to pump out of the pipeline.

        """
        self._exited += outputs

    @property
    def entered(self) -> int:
        """Instruction index

        `self` is this issue information record.

        """
        return self._entered

    @property
    def in_flight(self) -> bool:
        """True if there're in-flight instructions, otherwise False

        `self` is this issue information record.

        """
        return self._exited < self._entered


@attr.s(auto_attribs=True, frozen=True)
class _TransitionUtil:

    """Utilization transition of a single unit between two pulses"""

    old_util: typing.Collection[InstrState]

    new_util: Iterable[InstrState]


def _accept_instr(instr: int, inputs: Iterable[UnitModel],
                  util_info: BagValDict[ICaseString, InstrState]) -> bool:
    """Try to accept the given instruction to the unit.

    `instr` is the index of the instruction to try to accept.
    `inputs` are the input processing units to select from for issuing
             the instruction.
    `util_info` is the unit utilization information.
    The function tries to find an appropriate unit to issue the
    instruction to. It then updates the utilization information. It
    returns True if the instruction is issued to a unit, otherwise
    returns False.

    """
    acceptor = next(
        filter(lambda unit: _space_avail(unit, util_info), inputs), None)

    if not acceptor:
        return False

    util_info[acceptor.name].append(InstrState(instr))
    return True


def _add_access(instr: HwInstruction, instr_index: int,
                builders: Mapping[object, RegAccQBuilder]) -> None:
    """Append the instruction access to the given plan.

    `instr` is the instruction to append whose access to the access
            plan.
    `instr_index` is the instruction index.
    `builders` are the registry access plan builders.

    """
    _add_rd_access(instr_index, builders, instr.sources)
    _add_wr_access(instr_index, builders[instr.destination])


def _add_rd_access(instr: int, builders: Mapping[object, RegAccQBuilder],
                   registers: Iterable[object]) -> None:
    """Register the read access of the given registers.

    `instr` is the instruction index.
    `builders` are the registry access plan builders.
    `registers` are the registers which will be read-accessed.

    """
    for reg in registers:
        builders[reg].append(AccessType.READ, instr)


def _add_wr_access(instr: int, builder: RegAccQBuilder) -> None:
    """Register the write access of the given instruction.

    `instr` is the instruction index.
    `builder` is the access plan builder.

    """
    builder.append(AccessType.WRITE, instr)


def _build_acc_plan(program: Iterable[Tuple[int, HwInstruction]]) -> Dict[
        object, RegAccessQueue]:
    """Build the registry access plan through the program lifetime.

    `program` is the program to build a registry access plan for.
    The function returns the registry access plan.

    """
    builders: typing.DefaultDict[
        object, RegAccQBuilder] = collections.defaultdict(RegAccQBuilder)

    for instr_index, instr in program:
        _add_access(instr, instr_index, builders)

    return {reg: builder.create() for reg, builder in builders.items()}


def _build_cap_map(inputs: Iterable[UnitModel]) -> Dict[
        object, List[UnitModel]]:
    """Build the capability map for input units.

    `inputs` are the input processing units.

    """
    cap_map: Dict[object, List[UnitModel]] = {}

    for unit in inputs:
        for cap in unit.capabilities:
            cap_map.setdefault(cap, []).append(unit)

    return cap_map


def _calc_unstalled(instructions: Iterable[InstrState]) -> int:
    """Count the number of unstalled instructions.

    `instructions` are the list of instructions to count unstalled ones
                   in.

    """
    return container_utils.count_if(
        lambda instr: instr.stalled == StallState.NO_STALL, instructions)


def _chk_full_stall(
        old_util: object, new_util: object, consumed: object) -> None:
    """Check if the whole processor has stalled.

    `old_util` is the utilization information of the previous clock
               pulse.
    `new_util` is the utilization information of the current clock
               pulse.
    `consumed` is the number of instructions fed to the pipeline so far.
    The function analyzes old and new utilization information and throws
    a StallError if a full stall is detected.

    """
    if new_util == old_util:
        raise StallError("Processor stalled after being fed "
                         f"${StallError.STATE_KEY} instructions", consumed)


def _chk_hazards(old_util: BagValDict[_T, InstrState], new_util:
                 Iterable[Tuple[_T, Iterable[InstrState]]], name_unit_map:
                 Mapping[_T, UnitModel], program: Sequence[HwInstruction],
                 acc_queues: Mapping[object, RegAccessQueue]) -> None:
    """Check different types of hazards.

    `old_util` is the utilization information of the previous clock
               pulse.
    `new_util` is the utilization information of the current clock
               pulse.
    `name_unit_map` is the name-to-unit mapping.
    `program` is the master instruction list.
    `acc_queues` are the planned access queues for registers.
    The function analyzes old and new utilization information and marks
    stalled instructions appropriately according to idientified hazards.

    """
    reqs_to_clear: Dict[ICaseString, MutableSequence[object]] = {}

    for unit, new_unit_util in new_util:
        _stall_unit(name_unit_map[unit].lock_info, _TransitionUtil(
            old_util[unit], new_unit_util), program, acc_queues, reqs_to_clear)

    items_to_clear = reqs_to_clear.items()

    for reg, req_lst in items_to_clear:
        for cur_req in req_lst:
            acc_queues[reg].dequeue(cur_req)


def _clr_data_stall(wr_lock: bool, reg_clears: MutableSequence[object], instr:
                    object, old_unit_util: Iterable[InstrState]) -> StallState:
    """Clear the data stall condition for this instruction.

    `wr_lock` is the current unit write lock flag.
    `reg_clears` are the requests to be cleared from the register access
                 queue.
    `instr` is the index of the instruction to clear whose data stall
            condition.
    `old_unit_util` is the unit utilization information of the previous
                    clock pulse.

    """
    if wr_lock:
        _update_clears(reg_clears, instr)

    return StallState.STRUCTURAL if next(filter(
        lambda old_instr: old_instr.instr == instr and old_instr.stalled !=
        StallState.DATA, old_unit_util), None) else StallState.NO_STALL


def _clr_src_units(instructions: Iterable[_HostedInstr],
                   util_info: BagValDict[ICaseString, _T]) -> None:
    """Clear the utilization of units releasing instructions.

    `instructions` is the information of instructions being moved from
                   one unit to a predecessor, sorted by their program
                   index.
    `util_info` is the unit utilization information.
    The function clears the utilization information of units from which
    instructions were moved to predecessor units.

    """
    for cur_instr in instructions:
        del util_info[cur_instr.host][cur_instr.index_in_host]


def _count_outputs(outputs: Iterable[UnitModel],
                   util_info: BagValDict[ICaseString, InstrState]) -> int:
    """Count the number of unstalled outputs.

    `outputs` are all the output units.
    `util_info` is the unit utilization information.

    """
    return sum(map(
        lambda out_port: _calc_unstalled(util_info[out_port.name]), outputs))


def _fill_cp_util(
        processor: ProcessorDesc, program: Sequence[HwInstruction], util_info:
        BagValDict[ICaseString, InstrState], issue_rec: _IssueInfo) -> None:
    """Calculate the utilization of a new clock pulse.

    `processor` is the processor to fill the utilization of whose units
                at the current clock pulse.
    `program` is the program to execute.
    `util_info` is the unit utilization information to fill.
    `issue_rec` is the issue record.

    """
    _flush_outputs(_get_out_ports(processor), util_info)
    _mov_flights(chain(
        processor.out_ports, processor.internal_units), program, util_info)
    _fill_inputs(
        _build_cap_map(chain(processor.in_out_ports, processor.in_ports)),
        program, util_info, issue_rec)


def _fill_inputs(cap_unit_map: Mapping[object, Iterable[UnitModel]],
                 program: Sequence[HwInstruction], util_info: BagValDict[
                     ICaseString, InstrState], issue_rec: _IssueInfo) -> None:
    """Fetch new program instructions into the pipeline.

    `cap_unit_map` is the mapping between capabilities and units.
    `program` is the program to fill the input units from whose
              instructions.
    `util_info` is the unit utilization information.
    `issue_rec` is the issue record.

    """
    prog_len = len(program)

    while issue_rec.entered < prog_len and _accept_instr(
            issue_rec.entered,
            cap_unit_map.get(program[issue_rec.entered].categ, []), util_info):
        issue_rec.bump_input()


def _fill_unit(unit: FuncUnit, program: Sequence[HwInstruction],
               util_info: BagValDict[ICaseString, InstrState]) -> None:
    """Fill an output with instructions from its predecessors.

    `unit` is the destination unit to fill.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = _get_candidates(unit, program, util_info)
    # instructions sorted by program index
    _mov_candidates(candidates, unit.model.name, util_info)
    # Need to sort instructions by their index in the host in a
    # descending order.
    _clr_src_units(sorted(candidates, key=lambda candid: candid.index_in_host,
                          reverse=True), util_info)


def _flush_output(out_instr_lst: MutableSequence[InstrState]) -> None:
    """Flush the output unit in preparation for a new cycle.

    `out_instr_lst` is the list of instructions in the output unit.

    """
    instr_indices = reversed(range(len(out_instr_lst)))

    for instr_index in instr_indices:
        if out_instr_lst[instr_index].stalled == StallState.NO_STALL:
            del out_instr_lst[instr_index]


def _flush_outputs(out_units: Iterable[UnitModel],
                   util_info: BagValDict[ICaseString, InstrState]) -> None:
    """Flush output units in preparation for a new cycle.

    `out_units` are the output processing units.
    `util_info` is the unit utilization information.

    """
    for cur_out in out_units:
        _flush_output(util_info[cur_out.name])


def _get_accepted(
        instructions: Iterable[InstrState], program: Sequence[HwInstruction],
        capabilities: typing.Container[object]) -> Iterator[int]:
    """Generate an iterator over compatible instructions.

    `instructions` are the instructions to filter.
    `program` is the master instruction list.
    `capabilities` are the capabilities to match instructions against.
    The function returns an iterator over the instruction indices.

    """
    return map(operator.itemgetter(0), filter(
        lambda instr: instr[1].stalled != StallState.DATA and program[
            instr[1].instr].categ in capabilities, enumerate(instructions)))


def _get_candidates(
        unit: FuncUnit, program: Sequence[HwInstruction],
        util_info: BagValDict[ICaseString, InstrState]) -> List[_HostedInstr]:
    """Find candidate instructions in the predecessors of a unit.

    `unit` is the unit to match instructions from predecessors against.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = (_get_new_guests(pred.name, _get_accepted(
        util_info[pred.name], program, unit.model.capabilities)) for
                  pred in unit.predecessors if pred.name in util_info)
    return heapq.nsmallest(
        _space_avail(unit.model, util_info), chain.from_iterable(candidates),
        key=lambda instr_info:
        util_info[instr_info.host][instr_info.index_in_host].instr)


def _get_new_guests(src_unit: ICaseString,
                    instructions: Iterable[int]) -> Iterator[_HostedInstr]:
    """Prepare new hosted instructions.

    `src_unit` is the old host of instructions.
    `instructions` are the new instructions to be hosted.

    """
    return map(lambda instr: _HostedInstr(src_unit, instr), instructions)


def _get_out_ports(processor: ProcessorDesc) -> "chain[UnitModel]":
    """Find all units at the processor output boundary.

    `processor` is the processor to find whose output ports.
    The function returns an iterable over all ports at the output
    boundary.

    """
    return chain(processor.in_out_ports,
                 map(lambda port: port.model, processor.out_ports))


def _mov_candidate(
        candidate: InstrState, unit_util: MutableSequence[InstrState]) -> None:
    """Move a candidate instruction between units.

    `candidate` is the candidate instruction to move.
    `unit_util` is the unit utilization information.

    """
    candidate.stalled = StallState.NO_STALL
    unit_util.append(candidate)


def _mov_candidates(candidates: Iterable[_HostedInstr], unit: ICaseString,
                    util_info: BagValDict[ICaseString, InstrState]) -> None:
    """Move candidate instructions between units.

    `candidates` are the candidate instructions to move.
    `unit` is the destination unit.
    `util_info` is the unit utilization information.

    """
    for cur_candid in candidates:
        _mov_candidate(util_info[cur_candid.host][cur_candid.index_in_host],
                       util_info[unit])


def _mov_flights(
        dst_units: Iterable[FuncUnit], program: Sequence[HwInstruction],
        util_info: BagValDict[ICaseString, InstrState]) -> None:
    """Move the instructions inside the pipeline.

    `dst_units` are the destination processing units.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    for cur_dst in dst_units:
        _fill_unit(cur_dst, program, util_info)


def _regs_accessed(rd_lock: bool, instr: object, registers: Iterable[object],
                   acc_queues: Mapping[object, RegAccessQueue]) -> bool:
    """Check if all needed registers can be accessed.

    `rd_lock` is the unit read lock.
    `instr` is the index of the instruction to check whose access to
            registers.
    `registers` are the instruction registers.
    `acc_queues` are the planned access queues for registers.

    """
    return not rd_lock or all(map(lambda src: acc_queues[src].can_access(
        AccessType.READ, instr), registers))


def _run_cycle(program: Sequence[HwInstruction],
               acc_queues: Mapping[object, RegAccessQueue], hw_info: HwSpec,
               util_tbl: MutableSequence[BagValDict[ICaseString, InstrState]],
               issue_rec: _IssueInfo) -> None:
    """Run a single clock cycle.

    `program` is the program to run whose instructions.
    `acc_queues` are the planned access queues for registers.
    `hw_info` is the processor information.
    `util_tbl` is the utilization table.
    `issue_rec` is the issue record.

    """
    old_util = util_tbl[-1] if util_tbl else BagValDict()
    cp_util = copy.deepcopy(old_util)
    _fill_cp_util(hw_info.processor_desc, program, cp_util, issue_rec)
    _chk_hazards(
        old_util, cp_util.items(), hw_info.name_unit_map, program, acc_queues)
    _chk_full_stall(old_util, cp_util, issue_rec.entered)
    issue_rec.pump_outputs(
        _count_outputs(_get_out_ports(hw_info.processor_desc), cp_util))
    util_tbl.append(cp_util)


def _space_avail(
        unit: UnitModel, util_info: BagValDict[ICaseString, _T]) -> int:
    """Calculate the free space for receiving instructions in the unit.

    `unit` is the unit to test whose free space.
    `util_info` is the unit utilization information.

    """
    return unit.width - len(util_info[unit.name])


def _stall_unit(
        unit_locks: processor_utils.units.LockInfo,
        trans_util: _TransitionUtil, program: Sequence[HwInstruction],
        acc_queues: Mapping[object, RegAccessQueue], reqs_to_clear:
        typing.MutableMapping[ICaseString, MutableSequence[object]]) -> None:
    """Mark instructions in the given unit as stalled as needed.

    `unit_locks` are the unit lock information.
    `trans_util` is the unit utilization transition information of the
                 current and previous clock pulses.
    `program` is the master instruction list.
    `acc_queues` are the planned access queues for registers.
    `reqs_to_clear` are the requests to be cleared from the access
                    queues.

    """
    for instr in trans_util.new_util:
        instr.stalled = _clr_data_stall(
            unit_locks.wr_lock, reqs_to_clear.setdefault(
                program[instr.instr].destination, []), instr.instr,
            trans_util.old_util) if _regs_accessed(
                unit_locks.rd_lock, instr.instr, program[
                    instr.instr].sources, acc_queues) else StallState.DATA


def _update_clears(reg_clears: MutableSequence[object], instr: object) -> None:
    """Update the list of register accesses to be cleared.

    `reqs_to_clear` are the requests to be cleared from the access
                    queues.
    `instr` is the index of the instruction to unstall.

    """
    reg_clears.append(instr)
