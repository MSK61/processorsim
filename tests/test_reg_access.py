#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests register access structures"""

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
# file:         test_reg_access.py
#
# function:     register access plan tests
#
# description:  tests register access plan creation
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.86.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from fastcore.foundation import mapt
import pydash
import pytest
from pytest import mark

from test_env import TEST_DIR
import reg_access
from reg_access import AccessGroup, AccessType, RegAccessQueue

_ACCESS_GR_CTOR = pydash.spread(AccessGroup)


class TestAccessPlan:
    """Test case for register access queues"""

    @mark.parametrize(
        "queue, result",
        [
            ([AccessGroup(AccessType.READ, [0])], True),
            ([AccessGroup(AccessType.WRITE, [0])], False),
            (
                mapt(
                    _ACCESS_GR_CTOR,
                    [[AccessType.WRITE, [1]], [AccessType.READ, [0]]],
                ),
                False,
            ),
            ([AccessGroup(AccessType.READ, [1])], False),
        ],
    )
    def test_access(self, queue, result):
        """Test requesting access.

        `self` is this test case.
        `queue` is the access queue under test.
        `result` is the request result.

        """
        assert RegAccessQueue(queue).can_access(AccessType.READ, 0) == result

    @mark.parametrize(
        "owner_groups, rem_owners",
        [([[0]], []), ([[0], [1]], [1]), ([[0, 1]], [1])],
    )
    def test_removing_requests(self, owner_groups, rem_owners):
        """Test removing requests.

        `self` is this test case.
        `owner_groups` are the initial queue request owner groups.
        `rem_owners` are the request owners remaining in the queue after
                     removal.

        """
        queue = RegAccessQueue(
            [AccessGroup(AccessType.READ, group) for group in owner_groups]
        )
        queue.dequeue(0)
        assert queue == RegAccessQueue(
            [AccessGroup(AccessType.READ, [owner]) for owner in rem_owners]
        )


class TestAddRequests:
    """Test case for adding requests"""

    @mark.parametrize(
        "reqs, result_queue",
        [
            (
                [[AccessType.READ, len(TEST_DIR)]],
                [AccessGroup(AccessType.READ, [len(TEST_DIR)])],
            ),
            ([[AccessType.WRITE, 0]], [AccessGroup(AccessType.WRITE, [0])]),
            (
                [[AccessType.READ, 0], [AccessType.WRITE, 1]],
                mapt(
                    _ACCESS_GR_CTOR,
                    [[AccessType.READ, [0]], [AccessType.WRITE, [1]]],
                ),
            ),
            (
                [[AccessType.WRITE, 0], [AccessType.WRITE, 1]],
                mapt(
                    _ACCESS_GR_CTOR,
                    [[AccessType.WRITE, [0]], [AccessType.WRITE, [1]]],
                ),
            ),
            (
                [[AccessType.WRITE, 0], [AccessType.READ, 1]],
                mapt(
                    _ACCESS_GR_CTOR,
                    [[AccessType.WRITE, [0]], [AccessType.READ, [1]]],
                ),
            ),
            (
                [[AccessType.READ, 0], [AccessType.READ, 1]],
                [AccessGroup(AccessType.READ, [0, 1])],
            ),
        ],
    )
    def test_adding_requests(self, reqs, result_queue):
        """Test adding requests.

        `self` is this test case.
        `reqs` are the requests to add.
        `result_queue` is the result queue.

        """
        builder = reg_access.RegAccQBuilder()

        for cur_req in reqs:
            builder.append(*cur_req)

        assert builder.create() == RegAccessQueue(result_queue)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
