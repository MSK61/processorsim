# -*- coding: utf-8 -*-

"""program definitions"""

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
# file:         programs_defs.py
#
# function:     program definitions
#
# description:  definitions needed for programs
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.6, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
from typing import Any

import attr

import container_utils


def _sorted_uniq(elems: collections.abc.Iterable[Any]) -> tuple[Any, ...]:
    """Sort the elements after filtering out duplicates.

    `elems` are the elements to filter and sort.

    """
    return container_utils.sorted_tuple(frozenset(elems))


@attr.frozen(repr=False)
class _Instruction:

    """Instruction"""

    sources: tuple[object, ...] = attr.ib(converter=_sorted_uniq)

    destination: object = attr.ib()


@attr.frozen
class HwInstruction(_Instruction):

    """Hardware instruction"""

    categ: object = attr.ib()


@attr.frozen
class ProgInstruction(_Instruction):

    """Program instruction"""

    name: str

    line: object
