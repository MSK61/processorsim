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
# environment:  Visual Studio Code 1.82.0, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

from collections import abc
import operator
from typing import Any, Final

import attr
import fastcore.foundation

import container_utils
from str_utils import ICaseString

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
    return container_utils.sorted_tuple(
        models, key=fastcore.foundation.Self.name()
    )


@attr.s(auto_attribs=True, frozen=True)
class LockInfo:

    """Parameter locking information in units"""

    rd_lock: object

    wr_lock: object


@attr.s(frozen=True)
class UnitModel:

    """Functional unit model"""

    def needs_mem(self, cap: ICaseString) -> object:
        """Test if the given capability will require memory access.

        `self` is this unit model.

        """
        return self.roles[cap]

    @property
    def capabilities(self) -> abc.KeysView[ICaseString]:
        """Unit capabilities

        `self` is this unit model.

        """
        return self.roles.keys()

    name: ICaseString = attr.ib()

    width: int = attr.ib()

    roles: abc.Mapping[ICaseString, object] = attr.ib()

    lock_info: LockInfo = attr.ib()


@attr.s(eq=False, frozen=True)
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

    model: UnitModel = attr.ib()

    predecessors: tuple[UnitModel, ...] = attr.ib(converter=sorted_models)
