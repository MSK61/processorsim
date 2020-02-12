#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
# pylint: enable=invalid-name

"""
simulates running a program through a processor architecture

Usage: processorSim.py --processor PROCESSORFILE PROGRAMFILE
"""

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
# file:         processorSim.py
#
# function:     assembly program execution simulator
#
# description:  runs an assembly program on a processor
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.42.0, python 3.7.6, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import itertools
import logging
import operator
import sys
import argparse
import typing
from typing import Collection, Dict, IO, Iterable, Iterator, List, Mapping, \
    Optional, Sequence, Sized, TextIO, Tuple

import attr
import more_itertools
from more_itertools import prepend

from container_utils import BagValDict
import hw_loading
import program_utils
import sim_services
from sim_services import InstrState, StallState
_COL_SEP = '\t'
# command-line option variables
# variable to receive the processor architecture file
_PROC_OPT_VAR = "processor_file"
_PROG_OPT_VAR = "prog_file"  # variable to receive the program file
_T = typing.TypeVar("_T")


def get_in_files(argv: Optional[Sequence[str]]) -> Tuple[TextIO, TextIO]:
    """Create input file objects from the given arguments.

    `argv` is the list of arguments.

    """
    args = process_command_line(argv)
    return typing.cast(Tuple[TextIO, TextIO],
                       operator.attrgetter(_PROC_OPT_VAR, _PROG_OPT_VAR)(args))


def get_sim_res(processor_file: IO[str],
                program_file: Iterable[str]) -> List[List[str]]:
    """Calculate the simulation result table.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    proc_desc = hw_loading.read_processor(processor_file)
    prog = program_utils.read_program(program_file)
    compiled_prog = program_utils.compile_program(prog, proc_desc.isa)
    proc_spec = sim_services.HwSpec(proc_desc.processor)
    return _get_sim_rows(
        enumerate(sim_services.simulate(compiled_prog, proc_spec)), len(prog))


def process_command_line(argv: Optional[Sequence[str]]) -> argparse.Namespace:
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the program.

    `argv` is the command-line arguments, defaulting to None.
    The function returns the program exit code.

    """
    processor_file, program_file = get_in_files(argv)
    logging.basicConfig(level=logging.INFO)
    with processor_file, program_file:
        run(processor_file, program_file)
    return 0        # success


def run(processor_file: IO[str], program_file: Iterable[str]) -> None:
    """Simulate the program on the given processor.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    _print_sim_res(get_sim_res(processor_file, program_file))


@attr.s(auto_attribs=True, frozen=True)
class _InstrPosition:

    """Instruction position"""

    def __str__(self) -> str:
        """Return the printable string of this instruction position.

        `self` is this instruction position.

        """
        return "{}:{}".format({StallState.NO_STALL: 'U', StallState.STRUCTURAL:
                               'S'}[self._stalled], self._unit)

    _unit: object

    _stalled: StallState


@attr.s(auto_attribs=True, frozen=True)
class _InstrFlight:

    """Instruction flight"""

    start_time: int

    stops: Iterable[_InstrPosition]


def _create_flight(instr_util: Mapping[int, _InstrPosition]) -> _InstrFlight:
    """Create an instruction flight from its utilization.

    `instr_util` is the instruction utilization information.

    """
    start_time = min(instr_util.keys())
    time_span = len(instr_util)
    return _InstrFlight(start_time, map(lambda clock_pulse: instr_util[
        clock_pulse], range(start_time, start_time + time_span)))


def _cui_to_flights(cxuxi: Iterable[Tuple[int, BagValDict[_T, InstrState]]],
                    instructions: int) -> Iterator[_InstrFlight]:
    """Convert a CxUxI utilization map to instruction flights.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    return _icu_to_flights(_cui_to_icu(cxuxi, instructions))


def _cui_to_icu(cxuxi: Iterable[Tuple[int, BagValDict[_T, InstrState]]],
                instructions: int) -> List[Dict[int, _InstrPosition]]:
    """Convert a CxUxI utilization map to IxCxU format.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` is the total number of instructions.

    """
    ixcxu: List[Dict[int, _InstrPosition]] = list(
        more_itertools.repeatfunc(dict, instructions))

    for cur_cp, uxi_util in cxuxi:
        _fill_cp_util(cur_cp, uxi_util.items(), ixcxu)

    return ixcxu


def _fill_cp_util(clock_pulse: int, cp_util: Iterable[
        Tuple[object, Iterable[InstrState]]], ixcxu: Sequence[
            typing.MutableMapping[int, _InstrPosition]]) -> None:
    """Fill the given clock utilization into the IxCxU map.

    `clock_pulse` is the clock pulse.
    `cp_util` is the clock pulse utilization information.
    `ixcxu` is the InstructionxClockxUnit utilization map to fill.

    """
    for unit, instr_lst in cp_util:
        for instr in instr_lst:
            ixcxu[instr.instr][clock_pulse] = _InstrPosition(
                unit, instr.stalled)


def _get_flight_row(flight: _InstrFlight) -> List[str]:
    """Convert the given flight to a row.

    `flight` is the flight to convert.

    """
    return [
        *(itertools.repeat("", flight.start_time)), *(map(str, flight.stops))]


def _get_last_tick(sim_res: Iterable[Sized]) -> int:
    """Calculate the last clock cycle in the simulation.

    `sim_res` is the simulation result.

    """
    return max(map(len, sim_res), default=0)


def _get_sim_rows(sim_res: Iterable[Tuple[int, BagValDict[_T, InstrState]]],
                  instructions: int) -> List[List[str]]:
    """Calculate the simulation rows.

    `sim_res` is the simulation result.
    `instructions` is the total number of instructions.

    """
    flights = _cui_to_flights(sim_res, instructions)
    return [_get_flight_row(flight) for flight in flights]


def _get_ticks(sim_res: Iterable[Sized]) -> Iterator[str]:
    """Retrieve the clock cycles.

    `sim_res` is the simulation result.
    The function calculates the clock cycles necessary to run the whole
    simulation and returns an iterator over them.

    """
    return map(str, range(1, _get_last_tick(sim_res) + 1))


def _icu_to_flights(ixcxu: Iterable[Mapping[int, _InstrPosition]]) -> Iterator[
        _InstrFlight]:
    """Convert a IxCxU utilization map to instruction flights.

    `ixcxu` is the InstructionxClockxUnit utilization map to convert.

    """
    return map(_create_flight, ixcxu)


def _print_res_row(instr: str, res_row: Iterable[str]) -> None:
    """Print the given simulation row.

    `instr` is the row instruction.
    `res_row` is the simulation row.

    """
    print(_COL_SEP.join(prepend(instr, res_row)))


def _print_sim_res(sim_res: Collection[Collection[str]]) -> None:
    """Print the simulation result.

    `sim_res` is the simulation result to print.

    """
    _print_tbl_hdr(sim_res)
    _print_tbl_data(enumerate(sim_res, 1))


def _print_tbl_data(sim_res: Iterable[Tuple[int, Iterable[str]]]) -> None:
    """Print the simulation table rows.

    `sim_res` is the simulation result.

    """
    for row_idx, fields in sim_res:
        _print_res_row('I' + str(row_idx), fields)


def _print_tbl_hdr(sim_res: Iterable[Sized]) -> None:
    """Print the simulation table header.

    `sim_res` is the simulation result.

    """
    ticks = _get_ticks(sim_res)
    print(_COL_SEP.join(prepend("", ticks)))


if __name__ == '__main__':
    sys.exit(main())
