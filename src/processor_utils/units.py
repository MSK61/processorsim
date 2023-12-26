# -*- coding: utf-8 -*-

"""processor execution units"""

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
# file:         units.py
#
# function:     processor execution units
#
# description:  contains processing unit definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.6, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from collections.abc import Iterable
import operator
from typing import Any, Final

import attr
import fastcore.foundation

from container_utils import sorted_tuple
from str_utils import ICaseString

# unit attributes
UNIT_CAPS_KEY: Final = "capabilities"
UNIT_MEM_KEY: Final = "memoryAccess"
UNIT_NAME_KEY: Final = "name"
# unit lock attributes
UNIT_RLOCK_KEY: Final = "readLock"
UNIT_WLOCK_KEY: Final = "writeLock"
UNIT_WIDTH_KEY: Final = "width"


def sorted_models(models: Iterable[Any]) -> tuple[Any, ...]:
    """Create a sorted list of the given models.

    `models` are the models to sort.

    """
    return sorted_tuple(models, key=fastcore.foundation.Self.name())


@attr.frozen
class LockInfo:

    """Parameter locking information in units"""

    rd_lock: object

    wr_lock: object


def _sorted_caps(caps: Iterable[Any]) -> tuple[Any, ...]:
    """Create a sorted list of the given capabilities.

    `caps` are the capabilities to sort.

    """
    return sorted_tuple(caps)


@attr.frozen
class UnitModel:

    """Functional unit model"""

    def needs_mem(self, cap: object) -> bool:
        """Test if the given capability will require memory access.

        `self` is this unit model.
        `cap` is the capabilitiy to check.

        """
        return cap in self._mem_acl

    name: ICaseString = attr.field()

    width: int = attr.field()

    capabilities: tuple[ICaseString, ...] = attr.field(converter=_sorted_caps)

    lock_info: LockInfo = attr.field()

    _mem_acl: tuple[object, ...] = attr.field(converter=sorted_tuple)


@attr.frozen(eq=False)
class FuncUnit:

    """Processing functional unit"""

    def __eq__(self, other: Any) -> Any:
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = (
            (model, len(predecessors))
            for model, predecessors in [
                (self.model, self.predecessors),
                (other.model, other.predecessors),
            ]
        )
        return operator.eq(*criteria) and all(
            map(operator.is_, self.predecessors, other.predecessors)
        )

    model: UnitModel = attr.field()

    predecessors: tuple[UnitModel, ...] = attr.field(converter=sorted_models)
