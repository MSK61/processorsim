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
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 26 (Twenty Six)
#               Komodo IDE, version 11.1.1 build 91089, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################

import itertools
import operator
import str_utils
from str_utils import get_obj_repr
__all__ = ["LockInfo", "FuncUnit", "UnitModel"]


class LockInfo:

    """Parameter locking information in units"""

    def __init__(self, rd_lock, wr_lock):
        """Set parameter locking information.

        `self` is this locking information.
        `rd_lock` is the read lock status.
        `wr_lock` is the write lock status.

        """
        self.rd_lock = rd_lock
        self.wr_lock = wr_lock

    def __eq__(self, other):
        """Test if the two locking information settings are identical.

        `self` is this locking information.
        `other` is the other locking information.

        """
        return (self.rd_lock, self.wr_lock) == (other.rd_lock, other.wr_lock)

    def __ne__(self, other):
        """Test if the two locking information settings are different.

        `self` is this locking information.
        `other` is the other locking information.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this locking information.

        `self` is this locking information.

        """
        return get_obj_repr(type(self).__name__, [self.rd_lock, self.wr_lock])


class FuncUnit(object):

    """Processing functional unit"""

    def __init__(self, model, preds):
        """Create a functional unit.

        `self` is this functional unit.
        `model` is the unit model.
        `preds` are the units whose outputs are connected to the input
                of this unit.

        """
        assert type(model) == UnitModel
        self._model = model
        self._preds = sorted_models(preds)

    def __eq__(self, other):
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = map(
            lambda attrs: (attrs[0], len(attrs[1])),
            [(self._model, self._preds), (other.model, other.predecessors)])
        return operator.eq(*criteria) and all(
            map(operator.is_, self._preds, other.predecessors))

    def __ne__(self, other):
        """Test if the two functional units are different.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this functional unit.

        `self` is this functional unit.

        """
        return get_obj_repr(type(self).__name__, [self._model, self._preds])

    @property
    def model(self):
        """Functional unit model

        `self` is this functional unit.

        """
        return self._model

    @property
    def predecessors(self):
        """Predecessor units of this functional unit

        `self` is this functional unit.

        """
        return self._preds


class UnitModel(object):

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
        assert all(map(lambda attr: type(attr) == str_utils.ICaseString,
                       itertools.chain([name], capabilities)))
        self._name = name
        self.width = width
        self._capabilities = tuple(sorted(capabilities))
        self.lock_info = lock_info

    def __eq__(self, other):
        """Test if the two functional unit models are identical.

        `self` is this functional unit model.
        `other` is the other functional unit model.

        """
        return (
            self._name, self.width, self._capabilities, self.lock_info) == (
            other.name, other.width, other.capabilities, other.lock_info)

    def __ne__(self, other):
        """Test if the two functional unit models are different.

        `self` is this functional unit model.
        `other` is the other functional unit model.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this functional unit model.

        `self` is this functional unit model.

        """
        return get_obj_repr(
            type(self).__name__,
            [self._name, self.width, self._capabilities, self.lock_info])

    @property
    def capabilities(self):
        """Unit model capabilities

        `self` is this functional unit model.

        """
        return self._capabilities

    @property
    def name(self):
        """Unit model name

        `self` is this functional unit model.

        """
        return self._name


def sorted_models(models):
    """Create a sorted list of the given models.

    `models` are the models to create a sorted list of.

    """
    return tuple(sorted(models, key=lambda model: model.name))
