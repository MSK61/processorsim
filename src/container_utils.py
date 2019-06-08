# -*- coding: utf-8 -*-

"""container utilities"""

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
# file:         container_utils.py
#
# function:     generic container utilities
#
# description:  contains helper container functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 11.1.1 build 91089, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################

import collections
from operator import eq, itemgetter
import str_utils


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

    def __delitem__(self, key):
        """Delete the list of the given key.

        `self` is this dictionary.
        `key` is the key to remove whose list.

        """
        if key in self._dict:  # Ignore non-existing keys.
            del self._dict[key]

    def __eq__(self, other):
        """Test if the two dictionaries are identical.

        `self` is this dictionary.
        `other` is the other dictionary.

        """
        assert type(other) is type(self)
        other_items = list(other.iteritems())
        lst_pairs = map(
            lambda pair: map(sorted, [pair[1], self[pair[0]]]), other_items)
        return eq(*map(len, [self, other_items])) and all(
            map(lambda elem_lists: eq(*elem_lists), lst_pairs))

    def __getitem__(self, key):
        """Retrieve the list of the given key.

        `self` is this dictionary.
        `key` is the key to retrieve whose list.

        """
        return self._dict[key]

    def __iter__(self):
        """Retrieve an iterator over this dictionary.

         `self` is this dictionary.

         """
        return iter(self._dict)

    def __len__(self):
        """Retrieve the number of keys in this dictionary.

        `self` is this dictionary.
        The function only considers keys with non-empty lists.

        """
        return sum(map(lambda item: 1, self.iteritems()))

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
        return str_utils.format_obj(type(self).__name__, [self._format_dict()])

    def iteritems(self):
        """Return the items of this dictionary.

        `self` is this dictionary.
        The function returns an iterator over dictionary items with
        non-empty lists.

        """
        return filter(itemgetter(1), self._dict.items())

    def _add_items(self, items):
        """Add items to this dictionary.

        `self` is this dictionary.
        `items` are the items to add.

        """
        for key, elem_lst in items:
            for elem in elem_lst:
                self[key].append(elem)

    def _format_dict(self):
        """Format this dictionary.

        `self` is this dictionary.

        """
        return "{{{}}}".format(self._format_elems())

    def _format_elems(self):
        """Format the elements of this dictionary.

        `self` is this dictionary.

        """
        items = map(lambda item: (item[0], sorted(item[1])), self.iteritems())
        item_strings = map(lambda item: "{}: {}".format(
            repr(item[0]), item[1]), sorted(items, key=itemgetter(0)))
        sep = ", "
        return sep.join(item_strings)


def concat_dicts(dict1, dict2):
    """Concatenate two dictionaries into a new one.

    `dict1` is the first dictionary.
    `dict2` is the second dictionary.

    """
    return dict(dict1, **dict2)


def contains(container, elems):
    """Test the membership of all elements within a container.

    `container` is the container to check elements against.
    `elems` are the elements to check.

    """
    return all(map(lambda cur_elem: cur_elem in container, elems))
