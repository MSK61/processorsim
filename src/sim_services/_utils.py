# -*- coding: utf-8 -*-

"""simulation helper utilities"""

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
# file:         _utils.py
#
# function:     space_avail
#
# description:  simulation helper utilities
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.47.1, python 3.8.3, Fedora release
#               32 (Thirty Two)
#
# notes:        This is a private program.
#
############################################################

import typing

import container_utils
import processor_utils.units
import str_utils
_T = typing.TypeVar("_T")


def space_avail(unit: processor_utils.units.UnitModel, util_info:
                container_utils.BagValDict[str_utils.ICaseString, _T]) -> int:
    """Calculate the free space for receiving instructions in the unit.

    `unit` is the unit to test whose free space.
    `util_info` is the unit utilization information.

    """
    return unit.width - len(util_info[unit.name])
