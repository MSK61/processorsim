# -*- coding: utf-8 -*-

"""program definitions"""

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
# file:         programs_defs.py
#
# function:     program definitions
#
# description:  definitions needed for programs
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 11.1.1 build 91033, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################

from str_conv import get_obj_repr


class Instruction(object):

    """Instruction"""

    def __init__(self, sources, dst):
        """Create an instruction.

        `self` is this instruction.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        self._sources = tuple(sorted(sources))
        self._dst = dst

    def __eq__(self, other):
        """Test if the two instructions are identical.

        `self` is this instruction.
        `other` is the other instruction.

        """
        return (self._sources, self._dst) == (other.sources, other.destination)

    def __ne__(self, other):
        """Test if the two instructions are different.

        `self` is this instruction.
        `other` is the other instruction.

        """
        return not self == other

    @property
    def destination(self):
        """Destination operand

        `self` is this instruction.

        """
        return self._dst

    @property
    def sources(self):
        """Source operands

        `self` is this instruction.

        """
        return self._sources


class HwInstruction(Instruction):

    """Hardware instruction"""

    def __init__(self, categ, sources, dst):
        """Create a hardware instruction.

        `self` is this hardware instruction.
        `categ` is the instruction category.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        Instruction.__init__(self, frozenset(sources), dst)
        self._categ = categ

    def __eq__(self, other):
        """Test if the two hardware instructions are identical.

        `self` is this hardware instruction.
        `other` is the other hardware instruction.

        """
        return Instruction.__eq__(self, other) and self._categ == other.categ

    def __ne__(self, other):
        """Test if the two hardware instructions are different.

        `self` is this hardware instruction.
        `other` is the other hardware instruction.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this hardware instruction.

        `self` is this hardware instruction.

        """
        return get_obj_repr(
            type(self).__name__, [self._categ, self._sources, self._dst])

    @property
    def categ(self):
        """Instruction category

        `self` is this hardware instruction.

        """
        return self._categ


class ProgInstruction(Instruction):

    """Program instruction"""

    def __init__(self, name, line, sources, dst):
        """Create a program instruction.

        `self` is this program instruction.
        `name` is the instruction name.
        `line` is the number of the line containing the instruction.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        Instruction.__init__(self, sources, dst)
        self._line = line
        self._name = name

    def __eq__(self, other):
        """Test if the two program instructions are identical.

        `self` is this program instruction.
        `other` is the other program instruction.

        """
        return Instruction.__eq__(self, other) and (
            self._line, self._name) == (other.line, other.name)

    def __ne__(self, other):
        """Test if the two program instructions are different.

        `self` is this program instruction.
        `other` is the other program instruction.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this program instruction.

        `self` is this program instruction.

        """
        return get_obj_repr(
            type(self).__name__, [self._name, self._sources, self._dst])

    @property
    def line(self):
        """Number of the source line containing the instruction

        `self` is this program instruction.

        """
        return self._line

    @property
    def name(self):
        """Instruction mnemonic

        `self` is this program instruction.

        """
        return self._name
