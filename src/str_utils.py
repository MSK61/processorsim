# -*- coding: utf-8 -*-

"""string utilities"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
import typing

import attr


def format_obj(
    cls_name: object, field_strings: collections.abc.Iterable[str]
) -> str:
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `field_strings` are the string representations of the object fields.

    """
    sep = ", "
    return f"{cls_name}({sep.join(field_strings)})"


@attr.frozen(auto_attribs=False, order=True)
class ICaseString:
    """Case-insensitive string"""

    def __contains__(self, item: str) -> bool:
        """Check if the item is a substring.

        `self` is this case-insensitive string.
        `item` is the substring to search for.

        """
        return self._GET_CANONICAL(item) in self._GET_CANONICAL(self.raw_str)

    def __str__(self) -> str:
        """Return the printable string of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return self.raw_str

    _GET_CANONICAL: typing.Final = staticmethod(str.lower)

    raw_str: str = attr.field(eq=_GET_CANONICAL, order=_GET_CANONICAL)
