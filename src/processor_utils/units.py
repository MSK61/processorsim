# -*- coding: utf-8 -*-

"""processor execution units"""

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
# file:         units.py
#
# function:     processor execution units
#
# description:  contains processing unit definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.89.0, python 3.11.9, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

from collections import abc
import operator
import typing
from typing import Any, Final

import attr
from attr import frozen
from fastcore import foundation

import container_utils

_T = typing.TypeVar("_T")
# unit attributes
UNIT_CAPS_KEY: Final = "capabilities"
UNIT_MEM_KEY: Final = "memoryAccess"
UNIT_NAME_KEY: Final = "name"
# unit lock attributes
UNIT_RLOCK_KEY: Final = "readLock"
UNIT_WLOCK_KEY: Final = "writeLock"
UNIT_ROLES_KEY: Final = "roles"
UNIT_WIDTH_KEY: Final = "width"


def sorted_models(models: abc.Iterable[Any]) -> tuple[Any, ...]:
    """Create a sorted list of the given models.

    `models` are the models to sort.

    """
    return container_utils.sorted_tuple(models, key=foundation.Self.name())


@frozen
class LockInfo:
    """Parameter locking information in units"""

    rd_lock: object

    wr_lock: object


@frozen
class UnitModel:
    """Functional unit model"""

    def needs_mem(self, cap: str) -> bool:
        """Test if the given capability will require memory access.

        `self` is this unit model.
        `cap` is the capabilitiy to check.

        """
        return typing.cast(bool, self.roles[cap])

    name: str

    width: int

    roles: abc.Mapping[str, object]

    lock_info: LockInfo


@frozen(eq=False)
class FuncUnit:
    """Processing functional unit"""

    def __eq__(self, other: Any) -> Any:
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        pair_attrs = (
            (
                attr_get_func(unit)
                for attr_get_func in [
                    foundation.Self.model(),
                    foundation.Self.predecessors(),
                ]
            )
            for unit in [self, other]
        )
        criteria = (
            (model, len(predecessors)) for model, predecessors in pair_attrs
        )
        return operator.eq(*criteria) and all(
            map(operator.is_, self.predecessors, other.predecessors)
        )

    model: UnitModel

    predecessors: tuple[UnitModel, ...] = attr.field(converter=sorted_models)
