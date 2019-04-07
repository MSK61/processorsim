# -*- coding: utf-8 -*-

"""string utilities"""

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
# file:         str_utils.py
#
# function:     generic string utilities
#
# description:  contains helper string functions and classes
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################

import itertools


class ICaseString:

    """Case-insensitive string"""

    _canonical = staticmethod(str.lower)

    def __init__(self, initial_str):
        """Create a case-insensitive string.

        `self` is this case-insensitive string.
        `initial_str` is the initial string content.

        """
        self.str = initial_str

    def __contains__(self, item):
        """Check if the item is a substring.

        `self` is this case-insensitive string.
        `item` is the substring to search for.

        """
        return self._canonical(item) in self._canonical(self.str)

    def __eq__(self, other):
        """Test if the two case-insensitive strings are identical.

        `self` is this case-insensitive string.
        `other` is the other case-insensitive string.

        """
        return self._canonical(self.str) == self._canonical(other.str)

    def __hash__(self):
        """Get the has value of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return hash(self._canonical(self.str))

    def __ne__(self, other):
        """Test if the two case-insensitive strings are different.

        `self` is this case-insensitive string.
        `other` is the other case-insensitive string.

        """
        return not self == other

    def __radd__(self, other):
        """Return the reflected concatenation result.

        `self` is this case-insensitive string.

        """
        return other + self.str

    def __repr__(self):
        """Return the official string of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return get_obj_repr(self.__class__.__name__, [self.str])

    def __str__(self):
        """Return the printable string of this case-insensitive string.

        `self` is this case-insensitive string.

        """
        return self.str


def format_obj(cls_name, field_strings):
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `field_strings` are the string representations of the object fields.

    """
    sep = ", "
    return '{}({})'.format(cls_name, sep.join(field_strings))


def get_obj_repr(cls_name, fields):
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `fields` are the object fields.

    """
    return format_obj(cls_name, itertools.imap(repr, fields))
