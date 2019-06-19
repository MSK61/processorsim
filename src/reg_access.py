# -*- coding: utf-8 -*-

"""register access"""

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
# file:         reg_access.py
#
# function:     register access forecast storage
#
# description:  stores expected register access requests
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import dataclasses
import enum
from enum import auto
import typing
from typing import List


class AccessType(enum.Enum):

    """Access type"""

    READ = auto()

    WRITE = auto()


@dataclasses.dataclass
class AccessGroup:

    """Access group"""

    def __init__(self, gr_type, initial_reqs=None):
        """Create an access group.

        `self` is this access group.
        `gr_type` is the request group type.
        `initial_reqs` is the initial request list, defaulting to an
                       empty list.

        """
        self.access_type = gr_type
        self.reqs = []

        if initial_reqs:
            self.reqs.extend(initial_reqs)

    access_type: AccessType

    reqs: List[int]


class RegAccessQueue(typing.NamedTuple):

    """Access request queue for a single register"""

    def can_access(self, req_type, req_owner):
        """Request access to the register.

        `self` is this access request queue.
        `req_type` is the request type.
        `req_owner` is the request owner.

        """
        return req_type == self.queue[0].access_type

    queue: List[AccessGroup]


class RegAccQBuilder:

    """Access request queue builder"""

    def __init__(self):
        """Create an access queue builder.

        `self` is this access queue builder.

        """
        self._queue = []

    def append(self, req_type, req_owner):
        """Append a new read request to the built queue.

        `self` is this access queue builder.
        `req_type` is the request type.
        `req_owner` is the request owner.

        """
        if not self._can_merge(req_type):
            self._queue.append(AccessGroup(req_type))

        self._queue[-1].reqs.append(req_owner)

    def create(self):
        """Create the request access queue.

        `self` is this access queue builder.

        """
        return RegAccessQueue(self._queue)

    def _can_merge(self, req_type):
        """Test if the given request can be merged with the last one.

        `self` is this access queue builder.
        `req_type` is the request type.

        """
        return req_type == AccessType.READ and self._queue and self._queue[
            -1].access_type == AccessType.READ
