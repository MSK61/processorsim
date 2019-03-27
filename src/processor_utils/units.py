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

from itertools import imap
import operator
from str_utils import get_obj_repr
__all__ = ["FuncUnit", "UnitModel"]


class FuncUnit(object):

    """Processing functional unit"""

    def __init__(self, model, preds):
        """Create a functional unit.

        `self` is this functional unit.
        `model` is the unit model.
        `preds` are the units whose outputs are connected to the input
                of this unit.

        """
        self.model = model
        self._preds = sorted_models(preds)

    def __eq__(self, other):
        """Test if the two functional units are identical.

        `self` is this functional unit.
        `other` is the other functional unit.

        """
        criteria = imap(
            lambda attrs: (attrs[0], len(attrs[1])),
            [(self.model, self._preds), (other.model, other.predecessors)])
        return operator.eq(*criteria) and all(
            imap(operator.is_, self._preds, other.predecessors))

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
        return get_obj_repr(type(self).__name__, [self.model, self._preds])

    @property
    def predecessors(self):
        """Predecessor units of this functional unit

        `self` is this functional unit.

        """
        return self._preds


class UnitModel(object):

    """Functional unit model"""

    def __init__(self, name, width, capabilities):
        """Create a functional unit model.

        `self` is this functional unit model.
        `name` is the unit model name.
        `width` is the unit model capacity.
        `capabilities` are the capabilities of instructions supported by
                       this unit model.

        """
        self.name = name
        self.width = width
        self._capabilities = tuple(sorted(capabilities))

    def __eq__(self, other):
        """Test if the two functional unit models are identical.

        `self` is this functional unit model.
        `other` is the other functional unit model.

        """
        return (self.name, self.width, self._capabilities) == (
            other.name, other.width, other.capabilities)

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
            type(self).__name__, [self.name, self.width, self._capabilities])

    @property
    def capabilities(self):
        """Unit model capabilities

        `self` is this functional unit model.

        """
        return self._capabilities


def sorted_models(models):
    """Create a sorted list of the given models.

    `models` are the models to create a sorted list of.

    """
    return tuple(sorted(models, key=lambda model: model.name))
