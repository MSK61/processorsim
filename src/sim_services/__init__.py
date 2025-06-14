# -*- coding: utf-8 -*-

"""sim_services package"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025 Mohammed El-Afifi
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
# file:         __init__.py
#
# function:     sim_services package
#
# description:  sim_services package export file
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

from collections import defaultdict
import collections.abc
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
import copy
from itertools import chain
import typing
from typing import Any, TypeVar

from attr import field, frozen, mutable
from fastcore import basics
import more_itertools

from container_utils import BagValDict
import errors
from processor_utils import ProcessorDesc
import processor_utils.units
from processor_utils.units import LockInfo, UnitModel
from program_defs import HwInstruction
from reg_access import AccessType, RegAccessQueue, RegAccQBuilder
from . import _instr_sinks, _utils
from ._instr_sinks import IInstrSink
from .sim_defs import InstrState, StallState

_KT = TypeVar("_KT")
# By all means _ObjT and _T definitions below are equivalent, however
# _ObjT is needed for generic functions in whose signatures the type
# variable only appears once otherwise pylance issues a warning/error.
_ObjT = TypeVar("_ObjT", bound=object)
_T = TypeVar("_T")
_VT = TypeVar("_VT")


@errors.EXCEPTION
class StallError(errors.SimErrorBase):
    """Stalled processor error"""

    def __init__(self, msg_tmpl: str, stalled_state: object) -> None:
        """Create a stalled processor error.

        `self` is this stalled processor error.
        `msg_tmpl` is the error message format taking the stalled
                   processor state as a keyword argument.
        `stalled_state` is the stalled processor state.

        """
        self._init_simple(
            msg_tmpl, [errors.ErrorElement(self.STATE_KEY, stalled_state)]
        )

    processor_state: object = field()

    STATE_KEY: typing.Final = "state"  # parameter key in message format


@frozen
class HwSpec:
    """Hardware specification"""

    processor_desc: ProcessorDesc

    name_unit_map: dict[str, UnitModel] = field(init=False)

    # Casting to typing.Any because pylance can't detect default as a
    # member of attr.field.
    @typing.cast(Any, name_unit_map).default
    def _(self) -> dict[str, UnitModel]:
        """Build the name-to-unit mapping.

        `self` is this hardware specification.

        """
        models = chain(
            self.processor_desc.in_ports,
            self.processor_desc.in_out_ports,
            map(
                basics.Self.model(),
                chain(
                    self.processor_desc.out_ports,
                    self.processor_desc.internal_units,
                ),
            ),
        )
        return {unit.name: unit for unit in models}


def simulate(
    program: Sequence[HwInstruction], hw_info: HwSpec
) -> list[BagValDict[str, InstrState]]:
    """Run the given program on the processor.

    `program` is the program to run.
    `hw_info` is the processor information.
    The function returns the pipeline diagram.

    """
    util_tbl: list[BagValDict[str, InstrState]] = []
    acc_queues = _build_acc_plan(enumerate(program))
    issue_rec = _IssueInfo()
    prog_len = len(program)

    while issue_rec.entered < prog_len or issue_rec.in_flight:
        _run_cycle(program, acc_queues, hw_info, util_tbl, issue_rec)

    return util_tbl


@mutable
class _AcceptStatus:
    """Instruction acceptance status"""

    accepted: object = field(default=True, init=False)

    mem_used: object


@mutable
class _IssueInfo:
    """Instruction issue information record"""

    def bump_input(self) -> None:
        """Increment the entered instructions index.

        `self` is this issue information record.

        """
        self._entered += 1

    def pump_outputs(self, outputs: int) -> None:
        """Pump outputs out of the pipeline.

        `self` is this issue information record.
        `outputs` are the number of outputs to pump out of the pipeline.

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

    _entered: int = field(default=0, init=False)

    _exited: int = field(default=0, init=False)


@frozen
class _RegAvailState:
    """Registers availability state"""

    avail: object

    regs: Iterable[object]


@frozen
class _TransitionUtil:
    """Utilization transition of a single unit between two pulses"""

    old_util: collections.abc.Collection[InstrState]

    new_util: Iterable[InstrState]


def _accept_instr(
    issue_rec: _IssueInfo,
    instr_categ: object,
    input_iter: Iterator[UnitModel],
    util_info: BagValDict[str, InstrState],
    accept_res: _AcceptStatus,
) -> None:
    """Try to accept the next instruction to an input unit.

    `issue_rec` is the issue record.
    `instr_categ` is the next instruction category.
    `input_iter` is an iterator over the input processing units to
                 select from for issuing the instruction.
    `util_info` is the unit utilization information.
    `accept_res` is the instruction acceptance result.
    The function tries to find an appropriate unit to issue the
    instruction to. It then updates the utilization information.

    """
    accept_res.accepted = False
    more_itertools.consume(
        iter(
            lambda: _accept_in_unit(
                input_iter, instr_categ, accept_res, util_info, issue_rec
            ),
            True,
        )
    )


def _accept_in_unit(
    input_iter: Iterator[UnitModel],
    instr_categ: object,
    accept_res: _AcceptStatus,
    util_info: BagValDict[str, InstrState],
    issue_rec: _IssueInfo,
) -> bool:
    """Try to accept the next instruction to the given unit.

    `input_iter` is an iterator over the input processing units to
                 select from for issuing the instruction.
    `instr_categ` is the next instruction category.
    `accept_res` is the instruction acceptance result.
    `util_info` is the unit utilization information.
    `issue_rec` is the issue record.
    The function returns whether no more input units should be attempted
    to accept the instruction.

    """
    try:
        unit = next(input_iter)
    except StopIteration:
        return True
    mem_access = unit.needs_mem(instr_categ)

    if _utils.mem_unavail(accept_res.mem_used, mem_access) or _utils.unit_full(
        unit.width, util_info[unit.name]
    ):
        return False

    _issue_instr(util_info[unit.name], mem_access, issue_rec, accept_res)
    accept_res.accepted = True
    return True


def _add_access(
    instr: HwInstruction,
    instr_index: int,
    builders: Mapping[object, RegAccQBuilder],
) -> None:
    """Append the instruction access to the given plan.

    `instr` is the instruction to append whose access to the access
            plan.
    `instr_index` is the instruction index.
    `builders` are the registry access plan builders.

    """
    _add_rd_access(instr_index, builders, instr.sources)
    _add_wr_access(instr_index, builders[instr.destination])


def _add_rd_access(
    instr: int,
    builders: Mapping[object, RegAccQBuilder],
    registers: Iterable[object],
) -> None:
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


def _build_acc_plan(
    program: Iterable[Iterable[Any]],
) -> dict[object, RegAccessQueue]:
    """Build the registry access plan through the program lifetime.

    `program` is the program to build a registry access plan for.
    The function returns the registry access plan.

    """
    builders: defaultdict[object, RegAccQBuilder] = defaultdict(RegAccQBuilder)

    for instr_index, instr in program:
        _add_access(instr, instr_index, builders)

    return {reg: builder.create() for reg, builder in builders.items()}


def _build_cap_map(
    inputs: Iterable[UnitModel],
) -> dict[object, list[UnitModel]]:
    """Build the capability map for input units.

    `inputs` are the input processing units.

    """
    cap_map: dict[object, list[UnitModel]] = {}

    for unit in inputs:
        for cap in unit.capabilities:
            cap_map.setdefault(cap, []).append(unit)

    return cap_map


def _calc_unstalled(instructions: Iterable[InstrState]) -> int:
    """Count the number of unstalled instructions.

    `instructions` are the list of instructions to count unstalled ones
                   in.

    """
    return more_itertools.quantify(
        instructions, lambda instr: instr.stalled == StallState.NO_STALL
    )


def _chk_data_stall(
    unit_locks: LockInfo,
    instr_index: object,
    instr: HwInstruction,
    acc_queues: Mapping[object, RegAccessQueue],
    reqs_to_clear: MutableMapping[object, MutableSequence[object]],
) -> StallState:
    """Check if the instruction should have a data stall.

    `unit_locks` are the unit lock information.
    `instr_index` is the index of the instruction to check whose data
                  stall status.
    `instr` is the instruction to check whose data stall status.
    `acc_queues` are the planned access queues for registers.
    `reqs_to_clear` are the requests to be cleared from the access
                    queues.

    """
    avail_state = _regs_avail(unit_locks, instr_index, instr, acc_queues)

    if not avail_state.avail:
        return StallState.DATA

    _update_clears(reqs_to_clear, avail_state.regs, instr_index)
    return StallState.NO_STALL


def _chk_full_stall(
    old_util: object, new_util: object, util_tbl: object
) -> None:
    """Check if the whole processor has stalled.

    `old_util` is the utilization information of the previous clock
               pulse.
    `new_util` is the utilization information of the current clock
               pulse.
    `util_tbl` is the utilization table.
    The function analyzes old and new utilization information and throws
    a StallError if a full stall is detected.

    """
    if new_util == old_util:
        raise StallError(
            f"Processor stalled with utilization ${StallError.STATE_KEY}",
            util_tbl,
        )


def _chk_hazards(
    old_util: BagValDict[_T, InstrState],
    new_util: Iterable[Iterable[Any]],
    name_unit_map: Mapping[_T, UnitModel],
    program: Sequence[HwInstruction],
    acc_queues: Mapping[object, RegAccessQueue],
) -> None:
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
    reqs_to_clear: dict[object, MutableSequence[object]] = {}

    for unit, new_unit_util in new_util:
        _stall_unit(
            name_unit_map[unit].lock_info,
            _TransitionUtil(old_util[unit], new_unit_util),
            program,
            acc_queues,
            reqs_to_clear,
        )

    items_to_clear = reqs_to_clear.items()

    for reg, req_lst in items_to_clear:
        for cur_req in req_lst:
            acc_queues[reg].dequeue(cur_req)


def _chk_avail_regs(
    avail_regs: MutableSequence[Iterable[_T]],
    acc_queues: Mapping[_T, RegAccessQueue],
    lock: object,
    new_regs: Iterable[_T],
    req_params: Iterable[object],
) -> bool:
    """Check if the given registers can be accessed.

    `avail_regs` are the list of available registers.
    `lock` is the locking flag.
    `new_regs` are the potential registers to be added to the available
               registers list.
    `acc_queues` are the planned access queues for registers.
    `req_params` are the request parameters.

    """
    if not lock:
        return True

    if not all(acc_queues[reg].can_access(*req_params) for reg in new_regs):
        return False

    avail_regs.append(new_regs)
    return True


def _clr_src_units(
    instructions: Iterable[_instr_sinks.HostedInstr],
    util_info: BagValDict[str, _ObjT],
) -> None:
    """Clear the utilization of units releasing instructions.

    `instructions` are the information of instructions being moved from
                   one unit to a predecessor, sorted by their program
                   index.
    `util_info` is the unit utilization information.
    The function clears the utilization information of units from which
    instructions were moved to predecessor units.

    """
    for cur_instr in instructions:
        del util_info[cur_instr.host][cur_instr.index_in_host]


def _count_outputs(
    outputs: Iterable[str], util_info: BagValDict[str, InstrState]
) -> int:
    """Count the number of unstalled outputs.

    `outputs` are all the output units.
    `util_info` is the unit utilization information.

    """
    return sum(_calc_unstalled(util_info[out_port]) for out_port in outputs)


def _fill_cp_util(
    processor: ProcessorDesc,
    program: Sequence[HwInstruction],
    util_info: BagValDict[str, InstrState],
    issue_rec: _IssueInfo,
) -> None:
    """Calculate the utilization of a new clock pulse.

    `processor` is the processor to fill the utilization of whose units
                at the current clock pulse.
    `program` is the program to execute.
    `util_info` is the unit utilization information to fill.
    `issue_rec` is the issue record.

    """
    in_units = chain(processor.in_out_ports, processor.in_ports)
    dst_units = more_itertools.prepend(
        _instr_sinks.OutSink(_get_out_ports(processor)),
        (
            _instr_sinks.UnitSink(dst, program)
            for dst in chain(processor.out_ports, processor.internal_units)
        ),
    )
    _fill_inputs(
        _build_cap_map(processor_utils.units.sorted_models(in_units)),
        program,
        util_info,
        _mov_flights(dst_units, util_info),
        issue_rec,
    )


def _fill_inputs(
    cap_unit_map: Mapping[object, Iterable[UnitModel]],
    program: Sequence[HwInstruction],
    util_info: BagValDict[str, InstrState],
    mem_busy: object,
    issue_rec: _IssueInfo,
) -> None:
    """Fetch new program instructions into the pipeline.

    `cap_unit_map` is the mapping between capabilities and units.
    `program` is the program to fill the input units from whose
              instructions.
    `util_info` is the unit utilization information.
    `mem_busy` is the memory busy flag.
    `issue_rec` is the issue record.

    """
    prog_len = len(program)
    accept_res = _AcceptStatus(mem_busy)

    while issue_rec.entered < prog_len and accept_res.accepted:
        _accept_instr(
            issue_rec,
            program[issue_rec.entered].categ,
            iter(cap_unit_map.get(program[issue_rec.entered].categ, [])),
            util_info,
            accept_res,
        )


def _fill_unit(
    unit: IInstrSink, util_info: BagValDict[str, InstrState], mem_busy: object
) -> object:
    """Fill an output with instructions from its predecessors.

    `unit` is the destination unit to fill.
    `util_info` is the unit utilization information.
    `mem_busy` is the memory busy flag.
    The function returns a flag indicating if a memory access is
    currently in progess.

    """
    mov_res = unit.fill_unit(util_info, mem_busy)
    _clr_src_units(
        sorted(mov_res.moved, key=basics.Self.index_in_host(), reverse=True),
        util_info,
    )
    return mov_res.mem_used


def _get_out_ports(processor: ProcessorDesc) -> "map[str]":
    """Find all units at the processor output boundary.

    `processor` is the processor to find whose output ports.
    The function returns an iterable over all port names at the output
    boundary.

    """
    return map(
        basics.Self.name(),
        chain(
            processor.in_out_ports,
            (port.model for port in processor.out_ports),
        ),
    )


def _issue_instr(
    instr_lst: MutableSequence[InstrState],
    mem_access: object,
    issue_rec: _IssueInfo,
    accept_res: _AcceptStatus,
) -> None:
    """Issue the next instruction to the issue list.

    `instr_lst` is the list of hosted instructions in  a unit.
    `mem_access` is the hosting unit memory access flag.
    `issue_rec` is the issue record.
    `accept_res` is the instruction acceptance result.

    """
    instr_lst.append(InstrState(issue_rec.entered))
    issue_rec.bump_input()

    if mem_access:
        accept_res.mem_used = True


def _mov_flights(
    dst_units: Iterable[IInstrSink], util_info: BagValDict[str, InstrState]
) -> bool:
    """Move the instructions inside the pipeline.

    `dst_units` are the destination processing units.
    `util_info` is the unit utilization information.
    The function returns a flag indicating if a memory access is
    currently in progess.

    """
    mem_busy = False

    for cur_dst in dst_units:
        if _fill_unit(cur_dst, util_info, mem_busy):
            mem_busy = True

    return mem_busy


def _regs_avail(
    unit_locks: LockInfo,
    instr_index: object,
    instr: HwInstruction,
    acc_queues: Mapping[object, RegAccessQueue],
) -> _RegAvailState:
    """Check if all needed registers can be accessed.

    `unit_locks` are the unit lock information.
    `instr_index` is the index of the instruction to check whose access
                  to registers.
    `instr` is the instruction to check whose access to registers.
    `acc_queues` are the planned access queues for registers.
    The function returns the registers availability state.

    """
    avail_reg_lists: list[Iterable[object]] = []
    return (
        _RegAvailState(True, chain.from_iterable(avail_reg_lists))
        if all(
            _chk_avail_regs(avail_reg_lists, acc_queues, *chk_params)
            for chk_params in [
                (
                    unit_locks.rd_lock,
                    instr.sources,
                    [AccessType.READ, instr_index],
                ),
                (
                    unit_locks.wr_lock,
                    [instr.destination],
                    [AccessType.WRITE, instr_index],
                ),
            ]
        )
        else _RegAvailState(False, [])
    )


def _regs_loaded(
    old_unit_util: Iterable[InstrState], instr: object
) -> typing.Optional[InstrState]:
    """Check if the registers were previously loaded.

    `old_unit_util` is the unit utilization information of the previous
                    clock pulse.
    `instr` is the index of the instruction whose registers are to be
            checked for being previously loaded.

    """
    return more_itertools.first_true(
        old_unit_util,
        pred=lambda old_instr: old_instr.instr == instr
        and old_instr.stalled != StallState.DATA,
    )


def _run_cycle(
    program: Sequence[HwInstruction],
    acc_queues: Mapping[object, RegAccessQueue],
    hw_info: HwSpec,
    util_tbl: MutableSequence[BagValDict[str, InstrState]],
    issue_rec: _IssueInfo,
) -> None:
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
        old_util, cp_util.items(), hw_info.name_unit_map, program, acc_queues
    )
    _chk_full_stall(old_util, cp_util, util_tbl)
    issue_rec.pump_outputs(
        _count_outputs(_get_out_ports(hw_info.processor_desc), cp_util)
    )
    util_tbl.append(cp_util)


def _stall_unit(
    unit_locks: LockInfo,
    trans_util: _TransitionUtil,
    program: Sequence[HwInstruction],
    acc_queues: Mapping[object, RegAccessQueue],
    reqs_to_clear: MutableMapping[object, MutableSequence[object]],
) -> None:
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
        instr.stalled = (
            StallState.STRUCTURAL
            if _regs_loaded(trans_util.old_util, instr.instr)
            else _chk_data_stall(
                unit_locks,
                instr.instr,
                program[instr.instr],
                acc_queues,
                reqs_to_clear,
            )
        )


def _update_clears(
    reqs_to_clear: MutableMapping[_KT, MutableSequence[_VT]],
    regs: Iterable[_KT],
    instr: _VT,
) -> None:
    """Update the list of register accesses to be cleared.

    `reqs_to_clear` are the requests to be cleared from the access
                    queues.
    `regs` are the register whose access queues will be updated.
    `instr` is the index of the instruction to unstall.

    """
    for clr_reg in regs:
        reqs_to_clear.setdefault(clr_reg, []).append(instr)
