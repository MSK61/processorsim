# -*- coding: utf-8 -*-

"""wrappers for appeasing type checkers"""

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
# file:         test_type_chks.py
#
# function:     type checking clutches
#
# description:  contains wrappers for services that might upset type
#               checkers
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.6, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

import nbconvert.preprocessors
import nbformat

import program_defs


def create_hw_instr(regs, categ):
    """Create a hardware instruction.

    `regs` are the registers the instruction is operating on.
    `categ` is the instruction category.

    """
    # Pylance can't match packed arguments to the number of positional
    # arguments.
    srcs, dst = regs
    return program_defs.HwInstruction(srcs, dst, categ)


def exec_file(nb_file, run_path):
    """Execute a notebook file.

    `nb_file` is the notebook file to execute.
    `run_path` is the execution path.

    """
    nbconvert.preprocessors.ExecutePreprocessor().preprocess(
        nbformat.read(nb_file, nbformat.NO_CONVERT),
        {"metadata": {"path": run_path}},
    )
