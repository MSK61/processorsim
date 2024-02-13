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
# environment:  Visual Studio Code 1.86.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from collections import abc
from collections.abc import Iterable
import operator
from typing import Any, cast, Final

import attr
from attr import frozen
from fastcore import foundation

import container_utils
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
    return container_utils.sorted_tuple(models, key=foundation.Self.name())


@frozen
class LockInfo:
    """Parameter locking information in units"""

    rd_lock: object

    wr_lock: object


@frozen
class _UnitModel2:
    """Functional unit model"""

    def needs_mem(self, cap: ICaseString) -> bool:
        """Test if the given capability will require memory access.

        `self` is this unit model.
        `cap` is the capabilitiy to check.

        """
        return cast(bool, self.roles[cap])

    name: ICaseString

    width: int

    roles: abc.Mapping[ICaseString, object]

    lock_info: LockInfo


# Looks like mypy can't honor auto_detect=True in attr.frozen so I have
# to explicitly(and redundantly) use init=False.
@frozen(init=False)
class UnitModel:
    """Functional unit model"""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        name: ICaseString,
        width: int,
        capabilities: Iterable[Any],
        lock_info: LockInfo,
        mem_acl: Iterable[object],
    ) -> None:
        """Create a unit model.

        `self` is this unit model.
        `name` is the unit name.
        `width` is the unit width.
        `capabilities` are the unit capabilities.
        `lock_info` is the locking information.
        `mem_acl` is the memory access control list.

        """
        mem_acl = tuple(mem_acl)
        # Pylance and pylint can't detect __attrs_init__ as an injected
        # method.
        # pylint: disable-next=no-member
        self.__attrs_init__(  # type: ignore[reportGeneralTypeIssues]
            _UnitModel2(
                name,
                width,
                {cap: cap in mem_acl for cap in capabilities},
                lock_info,
            )
        )

    def needs_mem(self, cap: object) -> bool:
        """Test if the given capability will require memory access.

        `self` is this unit model.
        `cap` is the capabilitiy to check.

        """
        return cap in self._model2.roles and self._model2.needs_mem(
            cast(ICaseString, cap)
        )

    @property
    def capabilities(self) -> abc.KeysView[ICaseString]:
        """Unit capabilities

        `self` is this unit model.

        """
        return self._model2.roles.keys()

    @property
    def lock_info(self) -> LockInfo:
        """Unit locking information

        `self` is this unit model.

        """
        return self._model2.lock_info

    @property
    def name(self) -> ICaseString:
        """Unit name

        `self` is this unit model.

        """
        return self._model2.name

    @property
    def width(self) -> int:
        """Unit width

        `self` is this unit model.

        """
        return self._model2.width

    _model2: _UnitModel2


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
