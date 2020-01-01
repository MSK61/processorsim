# -*- coding: utf-8 -*-

"""processor execution units"""

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
# file:         units.py
#
# function:     processor execution units
#
# description:  contains processing unit definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.41.1, python 3.7.5, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import operator
from typing import Collection

import attr

from str_utils import ICaseString
__all__ = ["LockInfo", "FuncUnit", "UnitModel"]
# unit attributes
UNIT_CAPS_KEY = "capabilities"
UNIT_NAME_KEY = "name"
# unit lock attributes
UNIT_RLOCK_KEY = "readLock"
UNIT_WLOCK_KEY = "writeLock"
UNIT_WIDTH_KEY = "width"


def sorted_models(models):
    """Create a sorted list of the given models.

    `models` are the models to create a sorted list of.

    """
    return tuple(sorted(models, key=lambda model: model.name))


@attr.s(auto_attribs=True, frozen=True)
class LockInfo:

    """Parameter locking information in units"""

    rd_lock: bool

    wr_lock: bool


@attr.s(auto_attribs=True, frozen=True)
class UnitModel:

    """Functional unit model"""

    name: ICaseString

    width: int

    capabilities: Collection[ICaseString] = attr.ib(
        converter=lambda capabilities: tuple(sorted(capabilities)))

    lock_info: LockInfo


@attr.s(eq=False, frozen=True)
class FuncUnit:

    """Processing functional unit"""

    def __eq__(self, other):
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = map(lambda attrs: (attrs[0], len(attrs[1])), [(
            self.model, self.predecessors), (other.model, other.predecessors)])
        return operator.eq(*criteria) and all(
            map(operator.is_, self.predecessors, other.predecessors))

    model: UnitModel = attr.ib(
        validator=attr.validators.instance_of(UnitModel))

    predecessors: Collection[UnitModel] = attr.ib(converter=sorted_models)
