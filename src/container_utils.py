# -*- coding: utf-8 -*-

"""container utilities"""

############################################################
#
# Copyright 2017, 2019, 2020 Mohammed El-Afifi
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
# file:         container_utils.py
#
# function:     generic container utilities
#
# description:  contains helper container functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.41.1, python 3.7.6, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import collections
import itertools
from operator import eq, itemgetter

from str_utils import format_obj


def concat_dicts(dict1, dict2):
    """Concatenate two dictionaries into a new one.

    `dict1` is the first dictionary.
    `dict2` is the second dictionary.

    """
    return {**dict1, **dict2}


def count_if(pred, elems):
    """Count the number of elements matching the given predicate.

    `pred` is the matching predicate.
    `elems` is the iterator over elements to count matching ones in.

    """
    return sum(1 if pred(elem) else 0 for elem in elems)


def get_from_set(elem_set, elem):
    """Get an element from the given set, after adding it if needed.

    `elem_set` is the set.
    `elem` is the element.
    The function returns the element in this set if one exists, otherwise adds
    it and returns the newly added element.

    """
    std_elem = elem_set.get(elem)

    if std_elem:
        return std_elem

    elem_set.add(elem)
    return elem


class BagValDict:

    """Dictionary with(unsorted) lists as values"""

    def __init__(self, initial_dict=None):
        """Create an empty dictionary.

        `self` is this dictionary.
        `initial_dict` is the initial dictionary contents, defaulting to
                       an empty dictionary.

        """
        self._dict = collections.defaultdict(list)

        if initial_dict:
            self._add_items(initial_dict.items())

    def __contains__(self, item):
        """Check if the given key exists.

        `self` is this dictionary.
        `key` is the key to check whose existence.
        The method only considers existing keys with non-empty lists.

        """
        return item in self._dict and self[item]

    def __eq__(self, other):
        """Test if the two dictionaries are identical.

        `self` is this dictionary.
        `other` is the other dictionary.

        """
        assert type(other) is type(self)
        other_items = list(other.items())
        lst_pairs = map(
            lambda pair: map(sorted, [pair[1], self[pair[0]]]), other_items)
        return eq(*(map(len, [self, other_items]))) and all(
            itertools.starmap(eq, lst_pairs))

    def __getitem__(self, key):
        """Retrieve the list of the given key.

        `self` is this dictionary.
        `key` is the key to retrieve whose list.

        """
        return self._dict[key]

    def __ne__(self, other):
        """Test if the two dictionaries are different.

        `self` is this dictionary.
        `other` is the other dictionary.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this dictionary.

        `self` is this dictionary.

        """
        return format_obj(type(self).__name__, [self._format_dict()])

    def _add_items(self, elems):
        """Add items to this dictionary.

        `self` is this dictionary.
        `elems` are the items to add.

        """
        for key, elem_lst in elems:
            for elem in elem_lst:
                self[key].append(elem)

    def _count(self):
        """Count the number of elements in this dictionary.

        `self` is this dictionary.

        """
        return count_if(lambda elem: True, self.items())

    def _format_dict(self):
        """Format this dictionary.

        `self` is this dictionary.

        """
        return f"{{{self._format_elems()}}}"

    def _format_elems(self):
        """Format the elements of this dictionary.

        `self` is this dictionary.

        """
        elems = map(lambda item: (item[0], sorted(item[1])), self.items())
        item_strings = map(lambda item: f"{item[0]!r}: {item[1]}",
                           sorted(elems, key=itemgetter(0)))
        sep = ", "
        return sep.join(item_strings)

    def _useful_items(self):
        """Filter out items with empty value lists.

        `self` is this dictionary.
        The method returns an iterator over dictionary items with
        non-empty lists.

        """
        return filter(itemgetter(1), self._dict.items())

    items = _useful_items

    __len__ = _count


class _IndexedSetBase:

    """Indexed set base class"""

    def __init__(self, index_func):
        """Create an indexed set.

        `self` is this set.
        `index_func` is the index calculation function.

        """
        self._index_func = index_func
        self._std_form_map = {}

    def __repr__(self):
        """Return the official string of this indexed set.

        `self` is this indexed set.

        """
        return format_obj(type(self).__name__, map(repr, [self._std_form_map]))

    def get(self, elem):
        """Retrieve the elem in this set matching the given one.

        `self` is this set.
        `elem` is the element to look up in this set.
        The method returns the element in this set that matches the
        given one, or None if none exists.

        """
        return self._std_form_map.get(self._index_func(elem))

    def add(self, elem):
        """Add the given element to this set.

        `self` is this set.
        `elem` is the element to add.
        If the element already exists, it'll be overwritten.

        """
        self._std_form_map[self._index_func(elem)] = elem


class IndexedSet(_IndexedSetBase):

    """Indexed set"""


class SelfIndexSet(_IndexedSetBase):

    """Self-indexed string set"""

    def __init__(self):
        """Create a set with an identity conversion function.

        `self` is this set.

        """
        _IndexedSetBase.__init__(self, lambda elem: elem)
