# -*- coding: utf-8 -*-

"""processor services"""

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
# file:         processor.py
#
# function:     processor management services
#
# description:  loads processor description files and simulates program
#               execution
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 26 (Twenty Six)
#
# notes:        This is a private program.
#
############################################################

import copy
import itertools
from itertools import ifilter, imap
import processor_utils
import yaml


class HwDesc(object):

    """Hardware description"""

    def __init__(self, processor, isa):
        """Create a hardware description.

        `self` is this hardware description.
        `processor` is the processor description.
        `isa` is the instruction set architecture.

        """
        self._processor = processor
        self._isa = isa

    def __eq__(self, other):
        """Test if the two hardware descriptions are identical.

        `self` is this hardware description.
        `other` is the other hardware description.

        """
        return (self._processor, self._isa) == (other.processor, other.isa)

    def __ne__(self, other):
        """Test if the two hardware descriptions are different.

        `self` is this hardware description.
        `other` is the other hardware description.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this hardware description.

        `self` is this hardware description.

        """
        return '{}({}, {})'.format(
            type(self).__name__, self._processor, self._isa)

    @property
    def isa(self):
        """Instruction set architecture

        `self` is this hardware description.

        """
        return self._isa

    @property
    def processor(self):
        """Processor description

        `self` is this hardware description.

        """
        return self._processor


class _HostedInstr(object):

    """Instruction hosted inside a functional unit"""

    def __init__(self, unit, local_index):
        """Set hosted instruction information.

        `self` is this hosted instruction information.
        `unit` is the hosting functional unit.
        `local_index` is the instruction index in the host unit
                      execution buffer.

        """
        self._host = unit
        self._local_index = local_index

    @property
    def host(self):
        """Hosting functional util

        `self` is this hosted instruction information.

        """
        return self._host

    @property
    def index_in_host(self):
        """Instruction index in the host internal execution buffer

        `self` is this hosted instruction information.

        """
        return self._local_index


class _IssueInfo(object):

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


def read_processor(proc_file):
    """Read the processor description from the given file.

    `proc_file` is the YAML file containing the processor description.
    The function constructs necessary processing structures from the
    given processor description file. It returns a processor
    description.

    """
    yaml_desc = yaml.load(proc_file)
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


def _get_accepted(instructions, program, capabilities):
    """Generate an iterator over compatible instructions.

    `instructions` are the instructions to filter.
    `program` is the master instruction list.
    `capabilities` are the capabilities to match instructions against.
    The function returns an iterator over tuples of the instruction
    index and the instruction itself.

    """
    return ifilter(lambda instr: _instr_in_caps(program[instr[1]].categ.lower(
        ), capabilities), enumerate(instructions))


def _get_candidates(unit, program, util_info):
    """Find candidate instructions in the predecessors of a unit.

    `unit` is the unit to match instructions from predecessors against.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = imap(
        lambda src_unit:
            imap(lambda instr_info: _HostedInstr(src_unit.name, instr_info[0]),
                 _get_accepted(util_info[src_unit.name], program,
                               unit.model.capabilities)),
            ifilter(lambda pred: pred.name in util_info, unit.predecessors))
    return sorted(itertools.chain(*candidates), key=lambda instr_info:
                  util_info[instr_info.host][instr_info.index_in_host])


def _accept_instr(instr, instr_index, unit, util_info):
    """Try to accept the given instruction to the unit.

    `instr` is the lower-case instruction to try to accept.
    `instr_index` is the index of the instruction in the program.
    `unit` is the unit to accept the instruction to.
    `util_info` is the unit utilization information.
    The function assumes the target unit already has space to accept new
    instructions. It updates the utilization information and returns
    True if the instruction is accepted; otherwise returns False.

    """
    assert instr == instr.lower()

    if not _instr_in_caps(instr, unit.capabilities):
        return False

    _add_instr_util(instr_index, unit.name, util_info)
    return True


def _add_instr_util(instr_index, unit, util_info):
    """Register the given instruction in the unit.

    `instr_index` is the index of the instruction in the program.
    `unit` is the unit to register the instruction in.
    `util_info` is the unit utilization information.

    """
    util_info.setdefault(unit, []).append(instr_index)


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

    `instructions` is the information if instructions being moved from
                   one unit to a predecessor.
    `util_info` is the unit utilization information.
    The function clears the utilization information of units from which
    instructions were moved to predecessor units.

    """
    for cur_instr in instructions:
        _rm_util(util_info, cur_instr)


def _count_outputs(outputs, util_info):
    """Count the number of active outputs.

    `outputs` are all the output units.
    `util_info` is the unit utilization information.

    """
    return sum(imap(lambda out_port: len(util_info[out_port.name]) if
                    out_port.name in util_info else 0, outputs))


def _feed_instr(instr, hosting_info, unit, util_info):
    """Feed the given instruction to the given unit.

    `instr` is the lower-case instruction to feed.
    `hosting_info` is the instruction hosting information in its current
                   host unit.
    `unit` is the unit to feed the instruction into.
    `util_info` is the unit utilization information.
    The function updates the utilization information.

    """
    _add_instr_util(util_info[hosting_info.host][hosting_info.index_in_host],
                    unit, util_info)
    return 1


def _fill_cp_util(processor, program, util_info, issue_rec):
    """Calculate the utilization of a new clock pulse.

    `processor` is the processor to fill the utilization of whose units
                at the current clock pulse.
    `program` is the program to execute.
    `util_info` is the unit utilization information during the current
                clock pulse.
    `issue_rec` is the issue record.

    """
    out_ports = processor.in_out_ports + tuple(
        imap(lambda port: port.model, processor.out_ports))
    _flush_outputs(out_ports, util_info)
    _mov_flights(processor.out_ports, program, util_info)
    _fill_inputs(processor.in_out_ports + processor.in_ports, program,
                 util_info, issue_rec)
    issue_rec.pump_outputs(_count_outputs(out_ports, util_info))


def _fill_inputs(inputs, program, util_info, issue_rec):
    """Fetch new program instructions into the pipeline.

    `inputs` are the input processing units.
    `program` is the program to fill the input units from whose
              instructions.
    `util_info` is the unit utilization information.
    `issue_rec` is the issue record.

    """
    prog_len = len(program)

    while issue_rec.entered < prog_len and _issue_instr(
        program[issue_rec.entered].categ.lower(), issue_rec.entered, inputs,
            util_info):
        issue_rec.bump_input()


def _fill_unit(unit, program, util_info):
    """Fill an output with instructions from its predecessors.

    `unit` is the output unit to fill.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    candidates = _get_candidates(unit, program, util_info)
    _clr_src_units(
        itertools.islice(reversed(candidates), len(candidates) -
                         _mov_candidates(candidates, unit.model, program,
                                         util_info), None), util_info)


def _flush_outputs(out_units, unit_util):
    """Flush output units in preparation for a new cycle.

    `out_units` are the output processing units.
    `util_info` is the unit utilization information during the current
                clock pulse.

    """
    for cur_out in out_units:
        if cur_out.name in unit_util:
            del unit_util[cur_out.name]


def _instr_in_caps(instr, capabilities):
    """Determine if the instruction belongs to the given capabilities.

    `instr` is the lower-case instruction to test.
    `capabilities` are the capabilities to match the instruction
                   against.

    """
    assert instr == instr.lower()
    return instr in imap(str.lower, capabilities)


def _issue_instr(instr, instr_index, inputs, util_info):
    """Issue an instruction to an appropriate input unit.

    `instr` is the lower-case instruction to issue.
    `instr_index` is the index of the instruction to try to accept.
    `inputs` are the input processing units to select from for issuing
             the instruction.
    `util_info` is the unit utilization information.
    The function tries to find an appropriate unit to issue the
    instruction to. It then updates the utilization information. It
    returns True if the instruction is issued to a unit, otherwise
    returns False.

    """
    assert instr == instr.lower()
    return next(
        ifilter(lambda unit: _space_avail(unit, util_info) and _accept_instr(
            instr, instr_index, unit, util_info), inputs), False)


def _mov_flights(out_units, program, util_info):
    """Move the instructions inside the pipeline.

    `out_units` are the output processing units.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.

    """
    for cur_out in out_units:
        _fill_unit(cur_out, program, util_info)


def _mov_candidates(candidates, unit, program, util_info):
    """Move candidate instructions between units.

    `candidates` are the candidate instructions to move.
    `unit` is the destination unit.
    `program` is the master instruction list.
    `util_info` is the unit utilization information.
    The function returns the number of moved instructions.

    """
    cur_candid = 0
    num_of_candids = len(candidates)

    while _space_avail(unit, util_info) and cur_candid < num_of_candids:
        cur_candid += _feed_instr(
            program[util_info[candidates[cur_candid].host][
                candidates[cur_candid].index_in_host]].categ.lower(),
            candidates[cur_candid], unit.name, util_info)

    return cur_candid


def _rm_util(util_info, hosted_instr):
    """Remove the given instruction from the unit utilization.

    `util_info` is the current utilization of all units.
    `hosted_instr` is the hosted instruction information.

    """
    util_info[hosted_instr.host].pop(hosted_instr.index_in_host)

    if not util_info[hosted_instr.host]:
        del util_info[hosted_instr.host]


def _run_cycle(program, processor, util_tbl, issue_rec):
    """Run a single clock cycle.

    `program` is the program to run whose instructions.
    `processor` is the processor to run whose pipeline for a clock
                pulse.
    `util_tbl` is the utilization table.
    `issue_rec` is the issue record.

    """
    old_util = util_tbl[-1] if util_tbl else {}
    cp_util = copy.deepcopy(old_util)
    _fill_cp_util(processor, program, cp_util, issue_rec)
    _chk_stall(old_util, cp_util, issue_rec.entered)
    util_tbl.append(cp_util)


def _space_avail(unit, util_info):
    """Determine if the unit can still accept instructions.

    `unit` is the unit to test whose free space.
    `util_info` is the current utilization of all units.

    """
    return unit.name not in util_info or len(util_info[unit.name]) < unit.width
