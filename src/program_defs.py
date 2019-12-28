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
# environment:  Visual Studdio Code 1.41.1, python 3.7.5, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import typing

import attr

from str_utils import ICaseString


@attr.s(frozen=True, repr=False)
class _Instruction:

    """Instruction"""

    sources: typing.Tuple[ICaseString, ...] = attr.ib(
        converter=lambda src_regs: tuple(_sorted_uniq(src_regs)))

    destination: ICaseString = attr.ib()


@attr.s(frozen=True)
class HwInstruction(_Instruction):

    """Hardware instruction"""

    categ: ICaseString = attr.ib(
        validator=attr.validators.instance_of(ICaseString))


@attr.s(auto_attribs=True, frozen=True)
class ProgInstruction(_Instruction):

    """Program instruction"""

    name: str

    line: int


def _sorted_uniq(elems):
    """Sort the elements after filtering out duplicates.

    `elems` are the elements to filter and sort.

    """
    return sorted(frozenset(elems))
