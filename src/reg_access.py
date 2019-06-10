# -*- coding: utf-8 -*-

"""registry access"""

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
# function:     registry access forecast storage
#
# description:  stores expected registry access requests
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import collections
from operator import eq
import str_utils


class ReadAccess:

    """Read access record"""

    def __init__(self, initial_reqs):
        """Create a read access record.

        `self` is this read access record.
        `initial_reqs` is the non-empty initial request list.

        """
        assert initial_reqs
        self._reqs = initial_reqs

    def __eq__(self, other):
        """Test if the two read access records are identical.

        `self` is this read access record.
        `other` is the other read access record.

        """
        other_items = iter(other)
        return eq(*map(len, [self, other])) and all(
            map(lambda req_pair: eq(*req_pair), zip(self._reqs, other_items)))

    def __iter__(self):
        """Retrieve an iterator over this record.

        `self` is this read access record.

        """
        return iter(self._reqs)

    def __len__(self):
        """Retrieve the number of requests in this record.

        `self` is this read access record.

        """
        return len(self._reqs)

    def __ne__(self, other):
        """Test if the two read access records are different.

        `self` is this read access record.
        `other` is the other read access record.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this record.

        `self` is this read access record.

        """
        return str_utils.get_obj_repr(type(self).__name__, [self._reqs])


class RegAccessQueue:

    """Access request queue for a single registry"""

    def __init__(self, initial_reqs=None):
        """Create an access queue.

        `self` is this hardware description.
        `initial_reqs` is the initial request list, defaulting to an
                       empty list.

        """
        self._queue = collections.deque()

        if initial_reqs:
            self._queue.extend(initial_reqs)

    def __eq__(self, other):
        """Test if the two access queues are identical.

        `self` is this access request queue.
        `other` is the other access request queue.

        """
        other_items = iter(other)
        return eq(*map(len, [self, other])) and all(
            map(lambda req_pair: eq(*req_pair), zip(self._queue, other_items)))

    def __iter__(self):
        """Retrieve an iterator over this queue.

        `self` is this access request queue.

        """
        return iter(self._queue)

    def __len__(self):
        """Retrieve the number of requests in this queue.

        `self` is this access request queue.

        """
        return len(self._queue)

    def __ne__(self, other):
        """Test if the two access queues are different.

        `self` is this access request queue.
        `other` is the other access request queue.

        """
        return not self == other

    def __repr__(self):
        """Return the official string of this queue.

        `self` is this access request queue.

        """
        return str_utils.format_obj(
            type(self).__name__, [self._format_queue()])

    def add_read(self, req_owner):
        """Add a new read request to this queue.

        `self` is this access request queue.
        `req_owner` is the request owner.

        """
        self._queue.append(ReadAccess([req_owner]))

    def _format_queue(self):
        """Format this queue.

        `self` is this access request queue.

        """
        return "[{}]".format(self._format_reqs())

    def _format_reqs(self):
        """Format the requests of this queue.

        `self` is this access request queue.

        """
        sep = ", "
        return sep.join(map(repr, self._queue))
