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
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

from dataclasses import dataclass
from str_utils import ICaseString
import typing


@dataclass(repr=False)
class Instruction:

    """Instruction"""

    sources: typing.Any

    destination: str

    def __init__(self, sources, dst):
        """Create an instruction.

        `self` is this instruction.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        self.sources = tuple(sorted(sources))
        self.destination = dst


@dataclass
class HwInstruction(Instruction):

    """Hardware instruction"""

    def __init__(self, categ, sources, dst):
        """Create a hardware instruction.

        `self` is this hardware instruction.
        `categ` is the instruction category.
        `sources` are the source registers read by the instruction.
        `dst` is the register written by the instruction.

        """
        assert type(categ) == ICaseString
        Instruction.__init__(self, frozenset(sources), dst)
        self.categ = categ

    categ: ICaseString


@dataclass
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
        self.name = name
        self.line = line

    name: str

    line: int
