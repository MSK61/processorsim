# -*- coding: utf-8 -*-

"""simulation helper utilities"""

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
# file:         _utils.py
#
# function:     mem_unavail and unit_full
#
# description:  simulation helper utilities
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

import collections.abc


def mem_unavail(mem_busy: object, mem_req: object) -> object:
    """Check if the memory is unavailable for the given access.

    `mem_busy` is the memory busy flag.
    `mem_req` is the unit memory access request.

    """
    return mem_busy and mem_req


def unit_full(width: object, unit_util: collections.abc.Sized) -> bool:
    """Check if the unit is full.

    `width` is the unit width.
    `unit_util` is the unit utilization information.

    """
    return len(unit_util) == width
