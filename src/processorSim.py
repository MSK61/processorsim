#!/usr/bin/env python3
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
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

from itertools import chain
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


class _InstrFlight:

    """Instruction flight"""

    def __init__(self, start_time, units):
        """Create an instruction flight.

        `self` is this instruction flight.
        `start_time` is the time at which the instruction starts its
                     flight.
        `units` are the units the instruction will execute through, in
                order.

        """
        self.start_time = start_time
        self.stops = units


class _InstrPosition:

    """Instruction position"""

    def __init__(self, unit, stalled):
        """Create an instruction position.

        `self` is this instruction position.
        `unit` is the unit hosting the instruction.
        `stalled` is the instruction stall status.

        """
        self.unit = unit
        self.stalled = stalled


def get_in_files(argv):
    """Create input file objects from the given arguments.

    `argv` is the list of arguments.

    """
    args = process_command_line(argv)
    return operator.attrgetter(_PROC_OPT_VAR, _PROG_OPT_VAR)(args)


def get_sim_res(processor_file, program_file):
    """Calculate the simulation result table.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    proc_desc = processor.read_processor(processor_file)
    prog = program_utils.read_program(program_file)
    compiled_prog = program_utils.compile_program(prog, proc_desc.isa)
    return _get_sim_rows(
        enumerate(processor.simulate(compiled_prog, proc_desc.processor)),
        len(prog))


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
        '--processor', dest=_PROC_OPT_VAR, type=open, required=True,
        metavar="PROCESSORFILE",
        help='Read the processor architecture from this file.')
    parser.add_argument(      # program
        _PROG_OPT_VAR, type=open, metavar="PROGRAMFILE",
        help='Simulate this program file.')
    parser.add_argument(      # customized description; put --help last
        '-h', '--help', action='help',
        help='Show this help message and exit.')

    args = parser.parse_args(argv)

    return args


def main(argv=None):
    processor_file, program_file = get_in_files(argv)
    logging.basicConfig(level=logging.INFO)
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
    _print_sim_res(get_sim_res(processor_file, program_file))


def _create_flight(instr_util):
    """Create an instruction flight from its utilization.

    `instr_util` is the instruction utilization information.

    """
    start_time = min(instr_util.keys())
    time_span = len(instr_util)
    return _InstrFlight(
        start_time,
        map(instr_util.get, range(start_time, start_time + time_span)))


def _cui_to_flights(cxuxi, instructions):
    """Convert a CxUxI utilization map to instruction flights.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    return _icu_to_flights(_cui_to_icu(cxuxi, instructions))


def _cui_to_icu(cxuxi, instructions):
    """Convert a CxUxI utilization map to IxCxU format.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    ixcxu = list(map(lambda instr: {}, range(instructions)))

    for cur_cp, uxi_util in cxuxi:
        _fill_cp_util(cur_cp, uxi_util, ixcxu)

    return ixcxu


def _fill_cp_util(cp, cp_util, ixcxu):
    """Fill the given clock utilization into the IxCxU map.

    `cp` is the clock pulse.
    `cp_util` is the clock pulse utilization information.
    `ixcxu` is the InstructionxClockxUnit utilization map to fill.

    """
    for unit in cp_util:
        for instr in cp_util[unit]:
            ixcxu[instr.instr][cp] = _InstrPosition(unit, instr.stalled)


def _get_flight_row(flight):
    """Convert the given flight to a row.

    `flight` is the flight to convert.

    """
    stall_label = 'S'
    return [""] * flight.start_time + [stall_label if path_stop.stalled else (
            "U:" + path_stop.unit) for path_stop in flight.stops]


def _get_last_tick(sim_res):
    """Calculate the last clock cycle in the simulation.

    `sim_res` is the simulation result.

    """
    return max(chain([0], map(len, sim_res)))


def _get_sim_rows(sim_res, instructions):
    """Calculate the simulation rows.

    `sim_res` is the simulation result.
    `instructions` is the total number of instructions.

    """
    flights = _cui_to_flights(sim_res, instructions)
    return [_get_flight_row(flight) for flight in flights]


def _get_ticks(sim_res):
    """Retrieve the clock cycles.

    `sim_res` is the simulation result.
    The function calculates the clock cycles necessary to run the whole
    simulation and returns an iterator over them.

    """
    return map(str, range(1, _get_last_tick(sim_res) + 1))


def _icu_to_flights(ixcxu):
    """Convert a IxCxU utilization map to instruction flights.

    `ixcxu` is the InstructionxClockxUnit utilization map to convert.

    """
    return map(_create_flight, ixcxu)


def _print_res_row(row_index, res_row):
    """Print the given simulation row.

    `row_index` is the index of the simulation row.
    `res_row` is the simulation row.

    """
    row_index = str(row_index + 1)
    print(_COL_SEP.join(chain(['I' + row_index], res_row)))


def _print_sim_res(sim_res):
    """Print the simulation result.

    `sim_res` is the simulation result to print.

    """
    _print_tbl_hdr(sim_res)
    _print_tbl_data(enumerate(sim_res))


def _print_tbl_data(sim_res):
    """Print the simulation table rows.

    `sim_res` is the simulation result.

    """
    for res_row in sim_res:
        _print_res_row(*res_row)


def _print_tbl_hdr(sim_res):
    """Print the simulation table header.

    `sim_res` is the simulation result.

    """
    ticks = _get_ticks(sim_res)
    print(_COL_SEP.join(chain([""], ticks)))


if __name__ == '__main__':
    status = main()
    sys.exit(status)
