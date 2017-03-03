#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
simulates running a program through a processor architecture

Usage: processorSim.py --processor PROCESSORFILE PROGRAMFILE
"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see
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
#
# notes:        This is a private program.
#
############################################################

import itertools
import sys
import argparse
# command-line option variables
# variable to receive the processor architecture file
_PROC_OPT_VAR = "processor_file"
_PROG_OPT_VAR = "prog_file"  # variable to receive the program file

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
    run_args = itertools.imap(
        lambda opt: getattr(args, opt), [_PROC_OPT_VAR, _PROG_OPT_VAR])
    run(*run_args)
    return 0        # success


def run(processor_file, program_file):
    """Simulate the program on the given processor.

    `processor_file` is the file containing the processor architecture.
    `program_file` is the file containing the program to simulate.
    The function reads the program file and simulates its execution on
    the processor defined by the architecture provided in the given
    processor description file.

    """
    proc_desc, isa = _read_processor(processor_file)
    prog = _read_program(program_file)
    _print_sim_res(_simulate(_compile(prog, isa), proc_desc))


def _compile(prog, isa):
    """Compile the program using the given instruction set.

    `prog` is the program to compile.
    `isa` is the instruction set.
    The function validates and translates the given program into a
    sequence that can be directly fed into a processor understanding the
    given instruction set and returns that sequence.

    """
    pass


def _print_sim_res(sim_res):
    """Print the simulation result.

    `sim_res` is the simulation result.

    """
    pass


def _read_processor(proc_file):
    """Read the processor description from the given file.

    `proc_file` is the file containing the processor description.
    The function constructs necessary processing structures from the
    given processor description file. It returns a tuple of the
    processor description and the supported instruction set.

    """
    return None, None


def _read_program(prog_file):
    """Read the program stored in the given file.

    `prog_file` is the file containing the program.
    The function returns the program instructions.

    """
    pass


def _simulate(program, processor):
    """Run the given program on the processor.

    `program` is the program to run.
    `processor` is the processor to run the program on.
    The function returns the pipeline diagram.

    """
    pass


if __name__ == '__main__':
    status = main()
    sys.exit(status)
