# -*- coding: utf-8 -*-

"""low-level processor utilities"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# file:         processor_utils.py
#
# function:     low-level processor loading utilities
#
# description:  loads different entities inside a processor description
#               file
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

class FuncUnit:

    """Processing functional unit"""

    def __init__(self, name, width, capabilities, preds):
        """Create a functional unit.

        `self` is this functional unit.
        `name` is the unit name.
        `width` is the unit capacity.
        `capabilities` is the list of capabilities of instructions
                       supported by this unit.
        `preds` is the list of units whose outputs are connected to the
                input of this unit.

        """
        self._name = name
        self._width = width
        self._capabilities = frozenset(capabilities)
        self._preds = frozenset(preds)

    def __eq__(self, other):
        """Compare the equality of two functional units.

        `self` is this functional unit.
        `other` is this functional unit.

        """
        return self._name == other.name and self._width == other.width and \
                           self._capabilities == other.capabilities and \
                           self._preds == other.predecessors

    @property
    def capabilities(self):
        """Unit capabilities

        `self` is this functional unit.

        """
        return self._capabilities

    @property
    def name(self):
        """Unit name

        `self` is this functional unit.

        """
        return self._name

    @property
    def predecessors(self):
        """Unit name

        `self` is this functional unit.

        """
        return self._preds

    @property
    def width(self):
        """Unit width

        `self` is this functional unit.

        """
        return self._width


def load_proc_desc(raw_desc):
    """Transform the given raw description into a processor one.

    `raw_desc` is the raw description to extract a processor from.
    The function returns a list of the functional units constituting the
    processor. The order of the list dictates that the predecessor units
    of a unit always succeed the unit.

    """
    unit_sect = "units"
    return [FuncUnit(raw_desc[unit_sect][0]["name"],
                     raw_desc[unit_sect][0]["width"], [], [])]
