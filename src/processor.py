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

from itertools import imap
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


def read_processor(proc_file):
    """Read the processor description from the given file.

    `proc_file` is the YAML file containing the processor description.
    The function constructs necessary processing structures from the
    given processor description file. It returns a processor
    description.

    """
    with open(proc_file) as proc_file:
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
    capabilities = processor_utils.get_abilities(processor)
    return map(
        lambda instr_entry:
            dict(_get_util_map(processor.in_out_ports, instr_entry,
                               capabilities)), enumerate(program))


def _get_instr_idx(instr_entry, capabilities):
    """Retrieve the instruction index.

    `instr_entry` is the entry of the instruction to retrieve whose
                  index.
    `capabilities` are supported capabilities.
    The function validates the instruction against supported
    capabilities.

    """
    capabilities = imap(str.lower, capabilities)
    instr_info_idx = 1

    if instr_entry[instr_info_idx].categ.lower() in capabilities:
        return instr_entry[0]

    raise InvalidOpError(
        "Invalid operation {}", instr_entry[instr_info_idx].categ)


def _get_util_map(hw_units, instr_entry, capabilities):
    """Create a map whose all units point to the same instruction.

    `hw_units` are the processing units to create keys from.
    `instr_entry` is the entry of the single instruction to which all
                  units point to.
    `capabilities` are supported capabilities.
    The function returns an iterator over key-value pairs containing the
    given units all pointing to the given instruction.

    """
    return _make_unit_map(hw_units, _get_instr_idx(instr_entry, capabilities))


def _make_unit_map(hw_units, val):
    """Create a map whose all units point to the same value.

    `hw_units` are the processing units to create keys from.
    `val` is the single value to which all units point to.
    The function returns an iterator over key-value pairs containing the
    given units all pointing to the given value.

    """
    return imap(lambda unit: (unit.name, val), hw_units)
