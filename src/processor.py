# -*- coding: utf-8 -*-

"""processor services"""

############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
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
# file:         processor.py
#
# function:     processor management services
#
# description:  loads processor description files and simulates program
#               execution
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import container_utils
import copy
import dataclasses
import heapq
import itertools
import processor_utils
from str_utils import ICaseString
import typing
from typing import NamedTuple
import yaml


class HwDesc(NamedTuple):

    """Hardware description"""

    processor: processor_utils.ProcessorDesc

    isa: typing.Mapping[str, ICaseString]


@dataclasses.dataclass(order=True)
class InstrState:

    """Instruction state"""

    instr: int

    stalled: bool = False


class StallError(RuntimeError):

    """Stalled processor error"""

    def __init__(self, msg_tmpl, stalled_state):
        """Create a stalled processor error.

        `self` is this stalled processor error.
        `msg_tmpl` is the error format message taking the stalled
                   processor state as a positional argument.
        `stalled_state` is the stalled processor state.

        """
        RuntimeError.__init__(self, msg_tmpl.format(stalled_state))
        self._stalled_state = stalled_state

    @property
    def processor_state(self):
        """Stalled processor state

        `self` is this stalled processor error.

        """
        return self._stalled_state


class _HostedInstr(NamedTuple):

    """Instruction hosted inside a functional unit"""

    host: ICaseString

    index_in_host: int


class _IssueInfo:

    """Instruction issue information record"""

    def __init__(self):
        """Create an issue information record.

        `self` is this issue information record.

        """
        self._entered = 0
        self._exited = 0

    def bump_input(self):
        """Increment the entered instructions index.

        `self` is this issue information record.

        """
        self._entered += 1

    def pump_outputs(self, outputs):
        """Pump outputs out of the pipeline.

        `self` is this issue information record.
        `outputs` is the number of outputs to pump out of the pipeline.

        """
        self._exited += outputs

    @property
    def entered(self):
        """Instruction index

        `self` is this issue information record.

        """
        return self._entered

    @property
    def in_flight(self):
        """True if there're in-flight instructions, otherwise False

        `self` is this issue information record.

        """
        return self._exited < self._entered


def read_processor(proc_file):
    """Read the processor description from the given file.

    `proc_file` is the YAML file containing the processor description.
    The function constructs necessary processing structures from the
    given processor description file. It returns a processor
    description.

    """
    yaml_desc = yaml.safe_load(proc_file)
    microarch_key = "microarch"
    processor = processor_utils.load_proc_desc(yaml_desc[microarch_key])
    isa_key = "ISA"
    return HwDesc(processor, processor_utils.load_isa(
        yaml_desc[isa_key], processor_utils.get_abilities(processor)))


def simulate(program, processor):
    """Run the given program on the processor.

    `program` is the program to run.
    `processor` is the processor to run the program on.
    The function returns the pipeline diagram.

    """
    util_tbl = []
    issue_rec = _IssueInfo()
    prog_len = len(program)

    while issue_rec.entered < prog_len or issue_rec.in_flight:
        _run_cycle(program, processor, util_tbl, issue_rec)

    return util_tbl


def _accept_instr(instr, inputs, util_info):
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
    try:
        acceptor = next(
            filter(lambda unit: _space_avail(unit, util_info), inputs))
    except StopIteration:  # No unit accepted the instruction.
        return False
    util_info[acceptor.name].append(InstrState(instr))
    return True


def _build_cap_map(inputs):
    """Build the capability map for input units.

    `inputs` are the input processing units.

    """
    cap_map = {}

    for unit in inputs:
        for cap in unit.capabilities:
            cap_map.setdefault(cap, []).append(unit)

    return cap_map


def _chk_stall(old_util, new_util, consumed):
    """Check if the processor has stalled.

    `old_util` is the old utilization information of the previous clock
               pulse.
    `new_util` is the new utilization information of the current clock
               pulse.
    `consumed` is the number of instructions fed to the pipeline so far.
    The function analyzes old and new utilization information and throws
    a StallError if a stall is detected.

    """
    if new_util == old_util:
        raise StallError(
            "Processor stalled after being fed {} instructions", consumed)


def _clr_src_units(instructions, util_info):
    """Clear the utilization of units releasing instructions.

    `instructions` is the information of instructions being moved from
                   one unit to a predecessor, sorted by their program
                   index.
    `util_info` is the unit utilization information.
    The function clears the utilization information of units from which
    instructions were moved to predecessor units.

    """
    for cur_instr in instructions:
        util_info[cur_instr.host].pop(cur_instr.index_in_host)


def _count_outputs(outputs, util_info):
    """Count the number of active outputs.

    `outputs` are all the output units.
    `util_info` is the unit utilization information.

    """
    return sum(map(
        lambda out_port: _get_unit_util(out_port.name, util_info), outputs))


def _fill_cp_util(processor, program, util_info, issue_rec):
    """Calculate the utilization of a new clock pulse.

    `processor` is the processor to fill the utilization of whose units
                at the current clock pulse.
    `program` is the program to execute.
    `util_info` is the unit utilization information to fill.
    `issue_rec` is the issue record.

    """
    out_ports = processor.in_out_ports + tuple(
        map(lambda port: port.model, processor.out_ports))
    _flush_outputs(out_ports, util_info)
    _mov_flights(list(processor.out_ports) + processor.internal_units, program,
                 util_info)
    _stall_units(processor.in_ports, util_info)
    _fill_inputs(_build_cap_map(processor.in_out_ports + processor.in_ports),
                 program, util_info, issue_rec)
    issue_rec.pump_outputs(_count_outputs(out_ports, util_info))


def _fill_inputs(cap_unit_map, program, util_info, issue_rec):
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


def _fill_unit(unit, program, util_info):
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


def _flush_outputs(out_units, unit_util):
    """Flush output units in preparation for a new cycle.

    `out_units` are the output processing units.
    `unit_util` is the utilization information of the given unit.

    """
    for cur_out in out_units:
        del unit_util[cur_out.name]


def _get_accepted(instructions, program, capabilities):
    """Generate an iterator over compatible instructions.

    `instructions` are the instructions to filter.
    `program` is the master instruction list.
    `capabilities` are the capabilities to match instructions against.
    The function returns an iterator over tuples of the instruction
    index and the instruction itself.

    """
    return filter(lambda instr: program[instr[1].instr].categ in capabilities,
                  enumerate(instructions))


def _get_candidates(unit, program, util_info):
    """Find candidate instructions in the predecessors of a unit.

    `unit` is the unit to match instructions from predecessors against.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = map(
        lambda src_unit:
            map(lambda instr_info: _HostedInstr(src_unit.name, instr_info[0]),
                _get_accepted(util_info[src_unit.name], program,
                              unit.model.capabilities)),
            filter(lambda pred: pred.name in util_info, unit.predecessors))
    return heapq.nsmallest(
        _space_avail(unit.model, util_info), itertools.chain(*candidates),
        key=lambda instr_info:
            util_info[instr_info.host][instr_info.index_in_host].instr)


def _get_unit_util(unit, util_info):
    """Retrieve the given unit current utilization level.

    `unit` is the unit to get whose utilization level.
    `util_info` is the unit utilization information.

    """
    return len(util_info[unit])


def _mov_candidate(candidate, unit, util_info):
    """Move a candidate instruction between units.

    `candidate` is the candidate instruction to move.
    `unit` is the destination unit.
    `util_info` is the unit utilization information.

    """
    candidate.stalled = False
    util_info[unit].append(candidate)


def _mov_candidates(candidates, unit, util_info):
    """Move candidate instructions between units.

    `candidates` are the candidate instructions to move.
    `unit` is the destination unit.
    `util_info` is the unit utilization information.

    """
    for cur_candid in candidates:
        _mov_candidate(util_info[cur_candid.host][cur_candid.index_in_host],
                       unit, util_info)


def _mov_flights(dst_units, program, util_info):
    """Move the instructions inside the pipeline.

    `dst_units` are the destination processing units.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    for cur_dst in dst_units:
        _update_flights(cur_dst, program, util_info)


def _run_cycle(program, processor, util_tbl, issue_rec):
    """Run a single clock cycle.

    `program` is the program to run whose instructions.
    `processor` is the processor to run whose pipeline for a clock
                pulse.
    `util_tbl` is the utilization table.
    `issue_rec` is the issue record.

    """
    old_util = util_tbl[-1] if util_tbl else container_utils.BagValDict()
    cp_util = copy.deepcopy(old_util)
    _fill_cp_util(processor, program, cp_util, issue_rec)
    _chk_stall(old_util, cp_util, issue_rec.entered)
    util_tbl.append(cp_util)


def _space_avail(unit, util_info):
    """Calculate the free space for receiving instructions in the unit.

    `unit` is the unit to test whose free space.
    `util_info` is the unit utilization information.

    """
    return unit.width - _get_unit_util(unit.name, util_info)


def _stall_unit(unit, util_info):
    """Mark instructions in the given unit as stalled.

    `unit` is the unit to mark instructions in.
    `util_info` is the unit utilization information.

    """
    for instr in util_info[unit]:
        instr.stalled = True


def _stall_units(units, util_info):
    """Mark instructions in the given units as stalled.

    `units` are the units to mark instructions in.
    `util_info` is the unit utilization information.

    """
    for unit in units:
        _stall_unit(unit.name, util_info)


def _update_flights(unit, program, util_info):
    """Update instruction in the given unit.

    `unit` is the unit to update instructions in.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    _stall_unit(unit.model.name, util_info)
    _fill_unit(unit, program, util_info)
