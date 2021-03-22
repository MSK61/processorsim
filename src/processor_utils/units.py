# -*- coding: utf-8 -*-

"""processor execution units"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.54.3, python 3.8.7, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

import operator
import typing
from typing import Iterable, Tuple

import attr
from fastcore.foundation import Self

from container_utils import sorted_tuple
import str_utils
# unit attributes
UNIT_CAPS_KEY = "capabilities"
UNIT_MEM_KEY = "memoryAccess"
UNIT_NAME_KEY = "name"
# unit lock attributes
UNIT_RLOCK_KEY = "readLock"
UNIT_WLOCK_KEY = "writeLock"
UNIT_WIDTH_KEY = "width"


@attr.s(auto_attribs=True, frozen=True)
class CapabilityInfo:

    """Capability information"""

    name: object

    mem_access: bool


@attr.s(auto_attribs=True, frozen=True)
class LockInfo:

    """Parameter locking information in units"""

    rd_lock: bool

    wr_lock: bool


@attr.s(frozen=True)
class UnitModel:

    """Legacy functional unit model"""

    def needs_mem(self, cap: object) -> bool:
        """Test if the given capability will require memory access.

        `self` is this unit model.

        """
        return cap in self._mem_acl

    name: str_utils.ICaseString = attr.ib()

    width: int = attr.ib()

    capabilities: Tuple[object, ...] = attr.ib(converter=sorted_tuple)

    lock_info: LockInfo = attr.ib()

    _mem_acl: Tuple[object, ...] = attr.ib(converter=sorted_tuple)


def sorted_models(models: Iterable[object]) -> Tuple[UnitModel, ...]:
    """Create a sorted list of the given models.

    `models` are the models to create a sorted list of.

    """
    return sorted_tuple(models, key=Self.name())


@attr.s(eq=False, frozen=True)
class FuncUnit:

    """Processing functional unit"""

    def __eq__(self, other: typing.Any) -> bool:
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = ((model, len(predecessors)) for model, predecessors in [(
            self.model, self.predecessors), (other.model, other.predecessors)])
        return operator.eq(*criteria) and all(
            map(operator.is_, self.predecessors, other.predecessors))

    model: UnitModel = attr.ib()

    predecessors: Tuple[UnitModel, ...] = attr.ib(converter=sorted_models)


def _sorted_caps(capabilities: Iterable[object]) -> Tuple[CapabilityInfo, ...]:
    """Create a sorted list of the given capabilities.

    `capabilities` are the capabilities to create a sorted list of.

    """
    return sorted_tuple(capabilities, key=Self.name())


@attr.s(frozen=True)
class UnitModel2:

    """Functional unit model"""

    name: str_utils.ICaseString = attr.ib()

    width: int = attr.ib()

    capabilities: Tuple[CapabilityInfo, ...] = attr.ib(converter=_sorted_caps)

    lock_info: LockInfo = attr.ib()


def make_unit_model(unit2: UnitModel2) -> UnitModel:
    """Create a unit model.

    `unit2` is the new unit model.

    """
    return UnitModel(unit2.name, unit2.width, map(
        Self.name(), unit2.capabilities), unit2.lock_info, (
            cap.name for cap in unit2.capabilities if cap.mem_access))
