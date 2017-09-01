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

import itertools
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


class InvalidOpError(RuntimeError):

    """Invalid operation error"""

    def __init__(self, msg_tmpl, operation):
        """Create an invalid operation error.

        `self` is this invalid operation error.
        `msg_tmpl` is the error format message taking the invalid
                   operation as a positional argument.
        `operation` is the invalid operation.

        """
        RuntimeError.__init__(self, msg_tmpl.format(operation))
        self._operation = operation

    @property
    def operation(self):
        """Invalid operation

        `self` is this invalid operation error.

        """
        return self._operation


class _IssueInfo(object):

    """Instruction issue information record"""

    def __init__(self, instr_seq):
        """Create an issue information record.

        `self` is this issue information record.
        `instr_seq` is the sequence of instructions to be issued.

        """
        self._instr_seq = instr_seq
        self.bump_instr()

    def bump_instr(self):
        """Retrieve the next instruction.

        `self` is this issue information record.

        """
        try:
            self._instr = self._instr_seq.next()
        except StopIteration:
            self._instr_valid = False
        else:
            self._instr_valid = True

    def can_issue(self):
        """Determine if more instructions can be issued.

        `self` is this issue information record.
        Depending on the last issue operation as well as the program
        counter, the method determines if more instructions can be still
        issued.

        """
        return self.last_issue_good() and self.has_next_issue()

    def has_next_issue(self):
        """Determine if more instructions still need to be issued.

        `self` is this issue information record.

        """
        return self._instr_valid

    def last_issue_good(self):
        """Determine if the last issue operation was successful.

        `self` is this issue information record.

        """
        return self.unit >= 0

    @property
    def instr(self):
        """Instruction index

        `self` is this issue information record.

        """
        return self._instr


class _Unit(object):

    """Unit capabilities for executing instructions"""

    def __init__(self, name, instructions, capabilities):
        """Create a new unit.

        `self` is this unit.
        `name` is the unit name.
        `instructions` is the number of instructions that can be
                       executed simultaneously by the unit.
        `capabilities` are the capabilities of instructions supported by
                       this unit model.

        """
        self._name = name
        self._instructions = instructions
        self._capabilities = map(str.lower, capabilities)

    def exec_instr(self, instr):
        """Try to execute the instruction in this unit.

        `self` is this unit.
        `instr` is the lower-case instruction to test for execution.
        The method returns True if the instruction could be fed for
        execution to this unit, otherwise it returns False.

        """
        if not (self._instructions and instr in self._capabilities):
            return False

        self._instructions -= 1
        return True

    @property
    def name(self):
        """Unit name

        `self` is this unit.

        """
        return self._name


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
    issue_rec = _IssueInfo(enumerate(program))

    while issue_rec.has_next_issue():
        util_tbl.append(_chk_stall(util_tbl, _get_cp_util(
            processor.in_out_ports, issue_rec), issue_rec.instr[1].categ))

    return util_tbl


def _get_cp_util(hw_units, issue_rec):
    """Calculate the utilization of a new clock pulse.

    `hw_units` are the processing units to execute the program on.
    `issue_rec` is the issue record.
    The function returns utilization information for the next clock pulse.

    """
    util_info = {}
    hw_units = map(
        lambda unit: _Unit(unit.name, unit.width, unit.capabilities), hw_units)
    issue_rec.unit = 0

    while issue_rec.can_issue():
        _issue_instr(hw_units, util_info, issue_rec)

    return dict(itertools.imap(_sorted_val, util_info.iteritems()))


def _chk_stall(util_tbl, new_util, next_instr):
    """Check if the processor has stalled.

    `util_tbl` is the utilization table so far.
    `new_util` is the new utilization information of the current clock
               pulse.
    `next_instr` is the next instruction to be executed.
    The function analyzes existing and new utilization information and
    determines if the processor is in stall. It throws an InvalidOpError
    if the next instruction can't be executed due to a stall, otherwise
    returns the new utilization information.

    """
    if new_util == util_tbl[-1] if util_tbl else not new_util:
        raise InvalidOpError("Invalid operation {}", next_instr)

    return new_util


def _feed_instr(util_info, unit, issue_rec):
    """Feed an instruction to the designated unit.

    `util_info` is the unit utilization information during the current
                clock pulse.
    `unit` is the designated unit to feed the instruction into.
    `issue_rec` is the issue record.
    The function moves an instruction from the program to the designated
    unit.

    """
    util_info.setdefault(unit, []).append(issue_rec.instr[0])
    issue_rec.bump_instr()


def _find_unit(hw_units, capability):
    """Find the index of the first unit matching the given capability.

    `hw_units` are the processing units to search.
    `capability` is the lower-case capability to find a matching unit
                 for.
    The function returns the index of the first matching unit, or -1 if
    no matching unit is found.

    """
    num_of_units = len(hw_units)
    return next(itertools.ifilter(lambda unit_idx: hw_units[
        unit_idx].exec_instr(capability), xrange(num_of_units)), -1)


def _issue_instr(hw_units, util_info, issue_rec):
    """Issue an instruction to enter an appropriate hardware unit.

    `hw_units` are the processing units to select from.
    `util_info` is the unit utilization information during the current
                clock pulse.
    `issue_rec` is the issue record.
    The function tries to find an appropriate unit to issue the
    instruction to. It then updates the vacant instruction slots in the
    found unit and the utilization information and records the selected
    unit and the new instruction index in the issue record.

    """
    issue_rec.unit = _find_unit(hw_units, issue_rec.instr[1].categ.lower())

    if issue_rec.last_issue_good():
        _feed_instr(util_info, hw_units[issue_rec.unit].name, issue_rec)


def _sorted_val(entry):
    """Sort the value part of the given entry.

    `entry` is the key-value pair to sort whose value.
    The function returns the given key-value pair after sorting its
    value.

    """
    return entry[0], sorted(entry[1])
