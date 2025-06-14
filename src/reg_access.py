# -*- coding: utf-8 -*-

"""register access"""

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
# file:         reg_access.py
#
# function:     register access forecast storage
#
# description:  stores expected register access requests
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
import enum
from enum import auto
import typing

from attr import field, frozen


class AccessType(enum.Enum):
    """Access type"""

    READ = auto()

    WRITE = auto()


@frozen
class AccessGroup:
    """Access group"""

    access_type: object

    reqs: set[object] = field(converter=set, factory=set)


def _rev_groups(
    lst: collections.abc.Reversible[AccessGroup],
) -> list[AccessGroup]:
    """Return the reversed list of the given one.

    `lst` is the list to reverse.

    """
    return list(reversed(lst))


@frozen
class RegAccessQueue:
    """Access request queue for a single register"""

    def can_access(self, req_type: object, req_owner: object) -> bool:
        """Request access to the register.

        `self` is this access request queue.
        `req_type` is the request type.
        `req_owner` is the request owner.

        """
        return (
            req_type == self._queue[-1].access_type
            and req_owner in self._queue[-1].reqs
        )

    def dequeue(self, req_owner: object) -> None:
        """Remove a request from this queue.

        `self` is this access request queue.
        `req_owner` is the request owner.

        """
        self._queue[-1].reqs.remove(req_owner)

        if not self._queue[-1].reqs:
            del self._queue[-1]

    # Typically a queue pushes new elements at the back and removes old
    # elements from the front. Since this queue is going to support
    # removal only without addition, we reverse the given queue to make
    # the queue front at the list tail and make use of the fast access
    # to the list tail.
    _queue: list[AccessGroup] = field(converter=_rev_groups)


@frozen
class RegAccQBuilder:
    """Access request queue builder"""

    def append(self, req_type: AccessType, req_owner: int) -> None:
        """Append a new read request to the built queue.

        `self` is this access queue builder.
        `req_type` is the request type.
        `req_owner` is the request owner.

        """
        if not self._can_merge(req_type):
            self._queue.append(AccessGroup(req_type))

        self._queue[-1].reqs.add(req_owner)

    def create(self) -> RegAccessQueue:
        """Create the request access queue.

        `self` is this access queue builder.

        """
        return RegAccessQueue(self._queue)

    def _can_merge(self, req_type: object) -> bool:
        """Test if the given request can be merged with the last one.

        `self` is this access queue builder.
        `req_type` is the request type.

        """
        return (
            req_type == AccessType.READ
            and typing.cast(bool, self._queue)
            and self._queue[-1].access_type == AccessType.READ
        )

    _queue: list[AccessGroup] = field(factory=list, init=False)
