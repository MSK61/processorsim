# -*- coding: utf-8 -*-

"""program definitions"""

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
#
# notes:        This is a private program.
#
############################################################


class _Instruction(object):

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


class HwInstruction(_Instruction):

    """Hardware instruction"""

    def __init__(self, categ, sources, dst):
        """Create a hardware instruction.

        `self` is this hardware instruction.
        `categ` is the instruction category.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        _Instruction.__init__(self, sources, dst)
        self._categ = categ

    def __eq__(self, other):
        """Test if the two hardware instructions are identical.

        `self` is this hardware instruction.
        `other` is the other hardware instruction.

        """
        return _Instruction.__eq__(self, other) and self._categ == other.categ

    def __repr__(self):
        """Return the official string of this hardware instruction.

        `self` is this hardware instruction.

        """
        return '{}({}, {}, {})'.format(type(self).__name__, repr(self._categ),
                                       self._sources, repr(self._dst))

    @property
    def categ(self):
        """Instruction category

        `self` is this hardware instruction.

        """
        return self._categ


class ProgInstruction(_Instruction):

    """Program instruction"""

    def __init__(self, name, sources, dst):
        """Create a program instruction.

        `self` is this program instruction.
        `name` is the instruction name.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        _Instruction.__init__(self, sources, dst)
        self._name = name

    @property
    def name(self):
        """Instruction mnemonic

        `self` is this program instruction.

        """
        return self._name