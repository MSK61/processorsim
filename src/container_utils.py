# -*- coding: utf-8 -*-

"""container utilities"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.95.1, python 3.12.7, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import abc
from collections import defaultdict
import collections.abc
from collections.abc import Callable, Iterable
from itertools import starmap
from operator import eq, itemgetter
import typing
from typing import Any, Generic, Optional, TypeVar

from attr import field, frozen
import fastcore.basics
import more_itertools
import pydash

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


@frozen(repr=False)
class _IndexedSetBase(abc.ABC, Generic[_T]):
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

    _index_func: Callable[[_T], object]

    _std_form_map: dict[object, _T] = field(factory=dict, init=False)


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
    """Self-indexed set"""

    def __init__(self) -> None:
        """Create a set with an identity conversion function.

        `self` is this set.

        """
        super().__init__(pydash.identity)

    @classmethod
    def create(cls, elems: Iterable[_T]) -> typing.Self:
        """Create a self-indexed set from elements.

        `cls` is the self-indexed set class.
        `elems` are the elements to initially insert into the set.

        """
        res = cls()

        for cur_elem in elems:
            res.add(cur_elem)

        return res


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


@frozen(eq=False, repr=False)
class BagValDict(Generic[_KT, _VT]):
    """Dictionary with(unsorted) lists as values"""

    def __eq__(self, other: Any) -> Any:
        """Test if the two dictionaries are identical.

        `self` is this dictionary.
        `other` is the other dictionary.

        """
        assert type(other) is type(self)
        other_items = tuple(other.items())
        lst_pairs = (
            (fastcore.basics.Self(lst)(sorted) for lst in [val_lst, self[key]])
            for key, val_lst in other_items
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
        # Pylance isn't smart enough to figure out that self._dict[key]
        # has the same type as list[_VT].
        return typing.cast(list[_VT], self._dict[key])

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

    def items(self) -> "filter[tuple[_KT, list[_VT]]]":
        """Filter out items with empty value lists.

        `self` is this dictionary.
        The method returns an iterator over dictionary items with
        non-empty lists.

        """
        return filter(itemgetter(1), self._dict.items())

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
        elems = sorted(elems, key=itemgetter(0))
        return ", ".join(
            starmap(lambda key, val_lst: f"{key!r}: {val_lst}", elems)
        )

    # defaultdict isn't strictly required here, but pylance can't
    # understand that factory products are passed anyway to the
    # converter.
    _dict: defaultdict[_KT, list[_VT]] = field(
        converter=_val_lst_dict, factory=defaultdict
    )
