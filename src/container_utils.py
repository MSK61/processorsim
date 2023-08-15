# -*- coding: utf-8 -*-

"""container utilities"""

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
# file:         container_utils.py
#
# function:     generic container utilities
#
# description:  contains helper container functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.81.1, python 3.11.4, Fedora release
#               38 (Thirty Eight)
#
# notes:        This is a private program.
#
############################################################

from collections import defaultdict
import collections.abc
from collections.abc import Callable, Iterable
from itertools import starmap
import operator
from operator import eq
from typing import Any, Generic, Optional, TypeVar

import attr
import more_itertools
import pydash.functions

from str_utils import format_obj

_KT = TypeVar("_KT")
_T = TypeVar("_T")
_VT = TypeVar("_VT")


def sorted_tuple(
    elems: Iterable[Any], key: Optional[Callable[[Any], Any]] = None
) -> tuple[Any, ...]:
    """Sort the elements.

    `elems` are the elements to sort.
    `key` is the key function used for sorting, defaulting to None.

    """
    return tuple(sorted(elems, key=key))


@attr.s(frozen=True, repr=False)
class _IndexedSetBase(Generic[_T]):

    """Indexed set base class"""

    def __repr__(self) -> str:
        """Return the official string of this indexed set.

        `self` is this indexed set.

        """
        return format_obj(type(self).__name__, [repr(self._std_form_map)])

    def get(self, elem: _T) -> Optional[_T]:
        """Retrieve the elem in this set matching the given one.

        `self` is this set.
        `elem` is the element to look up in this set.
        The method returns the element in this set that matches the
        given one, or None if none exists.

        """
        return self._std_form_map.get(self._index_func(elem))

    def add(self, elem: _T) -> None:
        """Add the given element to this set.

        `self` is this set.
        `elem` is the element to add.
        If the element already exists, it'll be overwritten.

        """
        self._std_form_map[self._index_func(elem)] = elem

    _index_func: Callable[[_T], object] = attr.ib()

    _std_form_map: dict[object, _T] = attr.ib(factory=dict, init=False)


class IndexedSet(_IndexedSetBase[_T]):

    """Indexed set"""


def get_from_set(elem_set: IndexedSet[_T], elem: _T) -> _T:
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


class SelfIndexSet(_IndexedSetBase[_T]):

    """Self-indexed string set"""

    def __init__(self) -> None:
        """Create a set with an identity conversion function.

        `self` is this set.

        """
        super().__init__(lambda elem: elem)


def _sorted(seq: Iterable[Any]) -> list[Any]:
    """Create a sorted list of the given iterable.

    `seq` is the iterable to sort.
    As I don't want to rely on unstable API from typeshed, I'm just
    relaxing the checks against the item type of the given iterable.

    """
    return sorted(seq)


def _val_lst_dict(
    val_iter_dict: collections.abc.Mapping[Any, Iterable[Any]]
) -> defaultdict[Any, list[Any]]:
    """Convert the given value iterable dictionary to a value list one.

    `val_iter_dict` is the dictionary containing value iterables.

    """
    val_lst_dict = starmap(
        lambda key, val_lst: (key, list(val_lst)), val_iter_dict.items()
    )
    return defaultdict(list, val_lst_dict)


@attr.s(eq=False, frozen=True, repr=False)
class BagValDict(Generic[_KT, _VT]):

    """Dictionary with(unsorted) lists as values"""

    def __eq__(self, other: Any) -> bool:
        """Test if the two dictionaries are identical.

        `self` is this dictionary.
        `other` is the other dictionary.

        """
        assert type(other) is type(self)
        other_items = tuple(other.items())
        lst_pairs = (
            map(_sorted, [val_lst, self[key]]) for key, val_lst in other_items
        )
        item_lst_pair: list[collections.abc.Sized] = [self, other_items]
        return eq(*(len(item_lst) for item_lst in item_lst_pair)) and all(
            starmap(eq, lst_pairs)
        )

    def __getitem__(self, key: _KT) -> list[_VT]:
        """Retrieve the list of the given key.

        `self` is this dictionary.
        `key` is the key to retrieve whose list.

        """
        return self._dict[key]

    def __len__(self) -> int:
        """Count the number of elements in this dictionary.

        `self` is this dictionary.

        """
        return more_itertools.ilen(self.items())

    def __repr__(self) -> str:
        """Return the official string of this dictionary.

        `self` is this dictionary.

        """
        return format_obj(type(self).__name__, [self._format_dict()])

    def _format_dict(self) -> str:
        """Format this dictionary.

        `self` is this dictionary.

        """
        return f"{{{self._format_elems()}}}"

    def _format_elems(self) -> str:
        """Format the elements of this dictionary.

        `self` is this dictionary.

        """
        elems: Iterable[tuple[_KT, list[_VT]]] = starmap(
            lambda key, val_lst: (key, sorted(val_lst)), self.items()
        )
        elems = sorted(elems, key=operator.itemgetter(0))
        return ", ".join(
            starmap(lambda key, val_lst: f"{key!r}: {val_lst}", elems)
        )

    def _useful_items(self) -> "filter[tuple[_KT, list[_VT]]]":
        """Filter out items with empty value lists.

        `self` is this dictionary.
        The method returns an iterator over dictionary items with
        non-empty lists.

        """
        return filter(
            pydash.functions.Spread(lambda _, val_lst: val_lst),
            self._dict.items(),
        )

    items = _useful_items

    _dict: defaultdict[_KT, list[_VT]] = attr.ib(
        converter=_val_lst_dict, factory=dict
    )
