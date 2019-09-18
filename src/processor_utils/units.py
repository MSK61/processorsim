# -*- coding: utf-8 -*-

"""processor execution units"""

############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.38.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

from dataclasses import dataclass
import operator
import typing
from typing import Collection

from str_utils import ICaseString
__all__ = ["LockInfo", "FuncUnit", "UnitModel"]
# unit attributes
UNIT_CAPS_KEY = "capabilities"
UNIT_NAME_KEY = "name"
# unit lock attributes
UNIT_RLOCK_KEY = "readLock"
UNIT_WLOCK_KEY = "writeLock"
UNIT_WIDTH_KEY = "width"


class LockInfo(typing.NamedTuple):

    """Parameter locking information in units"""

    rd_lock: bool

    wr_lock: bool


@dataclass
class UnitModel:

    """Functional unit model"""

    def __init__(self, name, width, capabilities, lock_info):
        """Create a functional unit model.

        `self` is this functional unit model.
        `name` is the unit model name.
        `width` is the unit model capacity.
        `capabilities` are the capabilities of instructions supported by
                       this unit model.
        `lock_info` is the parameter locking information.

        """
        self.name = name
        self.width = width
        self.capabilities = tuple(sorted(capabilities))
        self.lock_info = lock_info

    name: ICaseString

    width: int

    capabilities: Collection[ICaseString]

    lock_info: LockInfo


@dataclass
class FuncUnit:

    """Processing functional unit"""

    def __init__(self, model, preds):
        """Create a functional unit.

        `self` is this functional unit.
        `model` is the unit model.
        `preds` are the units whose outputs are connected to the input
                of this unit.

        """
        assert isinstance(model, UnitModel)
        self.model = model
        self.predecessors = sorted_models(preds)

    def __eq__(self, other):
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = map(lambda attrs: (attrs[0], len(attrs[1])), [(
            self.model, self.predecessors), (other.model, other.predecessors)])
        return operator.eq(*criteria) and all(
            map(operator.is_, self.predecessors, other.predecessors))

    model: UnitModel

    predecessors: Collection[UnitModel]


def sorted_models(models):
    """Create a sorted list of the given models.

    `models` are the models to create a sorted list of.

    """
    return tuple(sorted(models, key=lambda model: model.name))
