#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
simulates running a program through a processor architecture

Usage: processorSim.py --processor PROCESSORFILE PROGRAMFILE
"""

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
# file:         processorSim.py
#
# function:     assembly program execution simulator
#
# description:  runs an assembly program on a processor
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
from itertools import chain, imap
import logging
import operator
import processor
import program_utils
import sys
import argparse
_COL_SEP = '\t'
# command-line option variables
# variable to receive the processor architecture file
_PROC_OPT_VAR = "processor_file"
_PROG_OPT_VAR = "prog_file"  # variable to receive the program file


class _InstrFlight(object):

    """Instruction flight"""

    def __init__(self, start_time, units):
        """Create an instruction flight.

        `self` is this instruction flight.
        `start_time` is the time at which the instruction starts its
                     flight.
        `units` are the units the instruction will execute through, in
                order.

        """
        self._start_time = start_time
        self._units = tuple(units)

    @property
    def start_time(self):
        """Instruction flight start time

        `self` is this instruction flight.

        """
        return self._start_time

    @property
    def units(self):
        """Instruction itinerary

        `self` is this instruction flight.

        """
        return self._units


def process_command_line(argv):
    """
    Return args object.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(
        add_help=False)

    # define options here:
    parser.add_argument(      # processor architecture file
        '--processor', dest=_PROC_OPT_VAR, type=file, required=True,
        metavar="PROCESSORFILE",
        help='Read the processor architecture from this file.')
    parser.add_argument(      # program
        _PROG_OPT_VAR, type=file, metavar="PROGRAMFILE",
        help='Simulate this program file.')
    parser.add_argument(      # customized description; put --help last
        '-h', '--help', action='help',
        help='Show this help message and exit.')

    args = parser.parse_args(argv)

    return args


def main(argv=None):
    args = process_command_line(argv)
    logging.basicConfig(level=logging.INFO)
    processor_file, program_file = operator.attrgetter(
        _PROC_OPT_VAR, _PROG_OPT_VAR)(args)
    with processor_file, program_file:
        run(processor_file, program_file)
    return 0        # success


def run(processor_file, program_file):
    """Simulate the program on the given processor.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    proc_desc = processor.read_processor(processor_file)
    prog = program_utils.read_program(program_file)
    _print_sim_res(processor.simulate(program_utils.compile_program(
        prog, proc_desc.isa), proc_desc.processor), len(prog))


def _create_flight(instr_util):
    """Create an instruction flight from its utilization.

    `instr_util` is the instruction utilization information.

    """
    start_time = min(instr_util.iterkeys())
    time_span = len(instr_util)
    return _InstrFlight(
        start_time,
        imap(instr_util.get, xrange(start_time, start_time + time_span)))


def _cui_to_flights(cxuxi, instructions):
    """Convert a CxUxI utilization map to instruction flights.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    return _icu_to_flights(_cui_to_icu(enumerate(cxuxi), instructions))


def _cui_to_icu(cxuxi, instructions):
    """Convert a CxUxI utilization map to IxCxU format.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    ixcxu = map(lambda instr: {}, xrange(instructions))

    for cur_cp, uxi_util in cxuxi:
        _fill_cp_util(cur_cp, uxi_util.iteritems(), ixcxu)

    return ixcxu


def _fill_cp_util(cp, cp_util, ixcxu):
    """Fill the given clock utilization into the IxCxU map.

    `cp` is the clock pulse.
    `cp_util` is the clock pulse utilization information.
    `ixcxu` is the InstructionxClockxUnit utilization map to fill.

    """
    for unit, instr_lst in cp_util:
        for instr in instr_lst:
            ixcxu[instr][cp] = unit


def _icu_to_flights(ixcxu):
    """Convert a IxCxU utilization map to instruction flights.

    `ixcxu` is the InstructionxClockxUnit utilization map to convert.

    """
    return map(_create_flight, ixcxu)


def _print_flight(flight_index, flight):
    """Print the given instruction flight.

    `flight_index` is the index of the flight to print.
    `flight` is the flight to print.

    """
    dead_time = ""
    print _COL_SEP.join(chain(['I' + str(flight_index + 1)], itertools.repeat(
        dead_time, flight.start_time), flight.units))


def _print_flights(flights):
    """Print the given instruction flights.

    `flights` are the instruction flights to print.

    """
    _print_tbl_hdr(flights)
    _print_tbl_data(enumerate(flights))


def _print_sim_res(sim_res, instructions):
    """Print the simulation result.

    `sim_res` is the simulation result to print.
    `instructions` is the total number of instructions.

    """
    _print_flights(_cui_to_flights(sim_res, instructions))


def _print_tbl_data(flights):
    """Print the flights table rows.

    `flights` are the instruction flight entries.

    """
    for cur_flight in flights:
        _print_flight(*cur_flight)


def _print_tbl_hdr(flights):
    """Print the flights table header.

    `flights` are the instruction flights.

    """
    end_times = imap(
        lambda flight: flight.start_time + len(flight.units), flights)
    time_span = xrange(1, max(chain([0], end_times)) + 1)
    print _COL_SEP.join(chain([""], imap(str, time_span)))


if __name__ == '__main__':
    status = main()
    sys.exit(status)
