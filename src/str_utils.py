# -*- coding: utf-8 -*-

"""string utilities"""

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
# file:         str_utils.py
#
# function:     generic string utilities
#
# description:  contains helper string functions and classes
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.74.2, python 3.11.1, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################

import functools
import operator
import typing

import attr


def format_obj(cls_name: object, field_strings: typing.Iterable[str]) -> str:
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `field_strings` are the string representations of the object fields.

    """
    sep = ", "
    return f"{cls_name}({sep.join(field_strings)})"


@functools.total_ordering
@attr.s(eq=False, frozen=True)
class ICaseString:

    """Case-insensitive string"""

    def __contains__(self, item: str) -> bool:
        """Check if the item is a substring.

        `self` is this case-insensitive string.
        `item` is the substring to search for.

        """
        return self._canonical(item) in self._canonical(self.raw_str)

    def __eq__(self, other: typing.Any) -> bool:
        """Test if the two case-insensitive strings are identical.

        `self` is this case-insensitive string.
        `other` is the other case-insensitive string.

        """
        return operator.eq(*(self._get_canonical(other.raw_str)))

    def __hash__(self) -> int:
        """Get the has value of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return hash(self._canonical(self.raw_str))

    def __lt__(self, other: "ICaseString") -> bool:
        """Test if this case-insensitive string is less than the other.

        `self` is this case-insensitive string.
        `other` is the other case-insensitive string.

        """
        return operator.lt(*(self._get_canonical(other.raw_str)))

    def __radd__(self, other: str) -> str:
        """Return the reflected concatenation result.

        `self` is this case-insensitive string.
        `other` is the other string.

        """
        return other + self.raw_str

    def __str__(self) -> str:
        """Return the printable string of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return self.raw_str

    def _get_canonical(self, other: str) -> "map[str]":
        """Return the canonical forms of this and the other strings.

        `self` is this case-insensitive string.
        `other` is the other string.

        """
        return map(self._canonical, [self.raw_str, other])

    raw_str: str = attr.ib()

    _canonical = staticmethod(str.lower)
