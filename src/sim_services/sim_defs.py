# -*- coding: utf-8 -*-

"""simulation definitions"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
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
# file:         sim_defs.py
#
# function:     simulation helper classes
#
# description:  simulation definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

import enum
from enum import auto
from typing import Final

import attr


class StallState(enum.Enum):

    """Instruction stalling state"""

    NO_STALL: Final = auto()

    STRUCTURAL: Final = auto()

    DATA: Final = auto()


@attr.s
class InstrState:

    """Instruction state"""

    instr: int = attr.ib()

    # default is indeed the first parameter but pylance doesn't honor it
    # as a positional argument in calls.
    stalled: StallState = attr.ib(default=StallState.NO_STALL)
