#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Disabling then immediately enabling again the invalid-name pylint
# check allows to skip pylint checking for the module name.
# pylint: disable=invalid-name
# pylint: enable=invalid-name

"""
simulates running a program through a processor architecture

Usage: processor_sim.py --processor PROCESSORFILE PROGRAMFILE
"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.92.0, python 3.11.9, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

from collections import abc
from collections.abc import Collection, Iterable, Mapping, Sized
import csv
import itertools
import logging
import sys
import typing
from typing import Annotated, Any, IO
import _csv

import attr
from attr import frozen
import more_itertools
import typer
from typer import FileText

import type_checking
import hw_loading
import program_utils
import sim_services

if typing.TYPE_CHECKING:
    import _typeshed


def main(
    processor_file: Annotated[
        FileText,
        typer.Option(
            "--processor",
            help="Read the processor architecture from this file.",
        ),
    ],
    program_file: Annotated[
        FileText, typer.Argument(help="Simulate this program file.")
    ],
) -> None:
    """Simulate running a program through a processor architecture."""
    logging.basicConfig(level=logging.INFO)
    run(processor_file, program_file)


def run(processor_file: IO[str], program_file: IO[str]) -> None:
    """Simulate the program on the given processor.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    with processor_file, program_file:
        type_checking.call(ResultWriter, sys.stdout).print_sim_res(
            _get_sim_res(processor_file, program_file)
        )


@frozen
class _InstrPosition:
    """Instruction position"""

    def __str__(self) -> str:
        """Return the printable string of this instruction position.

        `self` is this instruction position.

        """
        return f"{self._stalled}:{self._unit}"

    _unit: object

    _stalled: sim_services.sim_defs.StallState


@frozen
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
    return _InstrFlight(
        start_time,
        type_checking.map_ex(
            range(start_time, start_time + time_span),
            instr_util,
            _InstrPosition,
        ),
    )


def _create_writer(
    out_stream: "_typeshed.SupportsWrite[str]",
) -> "_csv._writer":
    """Create a CSV writer with the given backend stream.

    `out_stream` is the backend stream.

    """
    return csv.writer(out_stream, "excel-tab", lineterminator="\n")


@frozen
class ResultWriter:
    """Simulation result writer"""

    def print_sim_res(self, sim_res: Collection[Collection[Any]]) -> None:
        """Print the simulation result.

        `self` is this writer.
        `sim_res` is the simulation result to print.

        """
        self._print_tbl_hdr(sim_res)
        self._print_tbl_data(enumerate(sim_res, 1))

    @staticmethod
    def _get_last_tick(sim_res: Iterable[Sized]) -> int:
        """Calculate the last clock cycle in the simulation.

        `sim_res` is the simulation result.

        """
        return max(map(len, sim_res), default=0)

    @classmethod
    def _get_ticks(cls, sim_res: Iterable[Sized]) -> range:
        """Retrieve the clock cycles.

        `cls` is the writer class.
        `sim_res` is the simulation result.
        The method calculates the clock cycles necessary to run the
        whole simulation and returns an iterator over them.

        """
        return range(1, cls._get_last_tick(sim_res) + 1)

    def _print_res_row(self, row_key: Any, res_row: Iterable[Any]) -> None:
        """Print the given simulation row.

        `self` is this writer.
        `row_key` is the row key.
        `res_row` is the simulation row.

        """
        self._writer.writerow(more_itertools.prepend(row_key, res_row))

    def _print_tbl_data(self, sim_res: Iterable[Iterable[Any]]) -> None:
        """Print the simulation table rows.

        `self` is this writer.
        `sim_res` is the simulation result.

        """
        for row_idx, fields in sim_res:
            self._print_res_row("I" + str(row_idx), fields)

    def _print_tbl_hdr(self, sim_res: Iterable[Sized]) -> None:
        """Print the simulation table header.

        `self` is this writer.
        `sim_res` is the simulation result.

        """
        self._print_res_row("", self._get_ticks(sim_res))

    _writer: "_csv._writer" = attr.field(converter=_create_writer)


def _cui_to_flights(
    cxuxi: Iterable[Iterable[Any]], instructions: int
) -> "map[_InstrFlight]":
    """Convert a CxUxI utilization map to instruction flights.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` are the total number of instructions.

    """
    return _icu_to_flights(_cui_to_icu(cxuxi, instructions))


def _cui_to_icu(
    cxuxi: Iterable[Iterable[Any]], instructions: int
) -> list[dict[int, _InstrPosition]]:
    """Convert a CxUxI utilization map to IxCxU format.

    `cxuxi` is the ClockxUnitxInstruction utilization map to convert.
    `instructions` are the total number of instructions.

    """
    ixcxu: list[dict[int, _InstrPosition]] = list(
        more_itertools.repeatfunc(dict, instructions)
    )

    for cur_cp, uxi_util in cxuxi:
        _fill_cp_util(cur_cp, uxi_util.items(), ixcxu)

    return ixcxu


def _fill_cp_util(
    clock_pulse: int,
    cp_util: Iterable[Iterable[Iterable[sim_services.InstrState]]],
    ixcxu: abc.Sequence[abc.MutableMapping[int, _InstrPosition]],
) -> None:
    """Fill the given clock utilization into the IxCxU map.

    `clock_pulse` is the clock pulse.
    `cp_util` is the clock pulse utilization information.
    `ixcxu` is the InstructionxClockxUnit utilization map to fill.

    """
    for unit, instr_lst in cp_util:
        for instr in instr_lst:
            ixcxu[instr.instr][clock_pulse] = _InstrPosition(
                unit, instr.stalled
            )


def _get_flight_row(flight: _InstrFlight) -> list[str]:
    """Convert the given flight to a row.

    `flight` is the flight to convert.

    """
    return [
        *(itertools.repeat("", flight.start_time)),
        *(str(stop) for stop in flight.stops),
    ]


def _get_sim_res(
    processor_file: IO[str], program_file: Iterable[str]
) -> list[list[str]]:
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
        enumerate(sim_services.simulate(compiled_prog, proc_spec)), len(prog)
    )


def _get_sim_rows(
    sim_res: Iterable[Iterable[Any]], instructions: int
) -> list[list[str]]:
    """Calculate the simulation rows.

    `sim_res` is the simulation result.
    `instructions` are the total number of instructions.

    """
    flights = _cui_to_flights(sim_res, instructions)
    return [_get_flight_row(flight) for flight in flights]


def _icu_to_flights(
    ixcxu: Iterable[Mapping[int, _InstrPosition]]
) -> "map[_InstrFlight]":
    """Convert a IxCxU utilization map to instruction flights.

    `ixcxu` is the InstructionxClockxUnit utilization map to convert.

    """
    return map(_create_flight, ixcxu)


if __name__ == "__main__":
    typer.run(main)
