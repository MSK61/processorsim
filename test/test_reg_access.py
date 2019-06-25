#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests register access structures"""

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
# file:         test_reg_access.py
#
# function:     register access plan tests
#
# description:  tests register access plan creation
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import pytest
from pytest import mark
from test_env import TEST_DIR
import reg_access
from reg_access import AccessGroup, AccessType, RegAccessQueue
import typing


class _Request(typing.NamedTuple):

    """Single access request"""

    req_type: AccessType

    req_owner: int


class TestAccessPlan:

    """Test case for register access queues"""

    @mark.parametrize(
        "queue, result", [([AccessGroup(AccessType.READ, [0])], True), (
            [AccessGroup(AccessType.WRITE, [0])], False), (
            [AccessGroup(AccessType.WRITE, [1]), AccessGroup(AccessType.READ, [
                0])], False), ([AccessGroup(AccessType.READ, [1])], False)])
    def test_access(self, queue, result):
        """Test requesting access.

        `self` is this test case.
        `queue` is the access queue under test.
        `result` is the request result.

        """
        assert RegAccessQueue(queue).can_access(AccessType.READ, 0) == result

    @mark.parametrize("reqs, result_queue", [([_Request(AccessType.READ, len(
        TEST_DIR))], [AccessGroup(AccessType.READ, [len(TEST_DIR)])]),
        ([_Request(AccessType.WRITE, 0)], [AccessGroup(AccessType.WRITE, [
            0])]), ([_Request(AccessType.READ, 0), _Request(
                AccessType.WRITE, 1)], [AccessGroup(AccessType.READ, [0]),
                                        AccessGroup(AccessType.WRITE, [1])]),
        ([_Request(AccessType.WRITE, 0), _Request(AccessType.WRITE, 1)], [
            AccessGroup(AccessType.WRITE, [0]), AccessGroup(AccessType.WRITE, [
                1])]),
        ([_Request(AccessType.WRITE, 0), _Request(AccessType.READ, 1)], [
            AccessGroup(AccessType.WRITE, [0]), AccessGroup(AccessType.READ, [
                1])]),
        ([_Request(AccessType.READ, 0), _Request(AccessType.READ, 1)], [
            AccessGroup(AccessType.READ, [0, 1])])])
    def test_adding_requests_produces_suitable_queue(self, reqs, result_queue):
        """Test adding requests.

        `self` is this test case.
        `reqs` are the requests to add.
        `result_queue` is the result queue.

        """
        builder = reg_access.RegAccQBuilder()

        for cur_req in reqs:
            builder.append(cur_req.req_type, cur_req.req_owner)

        assert builder.create() == RegAccessQueue(result_queue)

    @mark.parametrize("req_owners, rem_owners", [([0], []), ([0, 1], [1])])
    def test_removing_request_removes_foremost_request_group(
            self, req_owners, rem_owners):
        """Test removing a request from a single-request group.

        `self` is this test case.
        `req_owners` are the initial queue request owners.
        `rem_owners` are the request owners remaining in the queue after
                     removal.

        """
        queue = RegAccessQueue(
            [AccessGroup(AccessType.READ, [owner]) for owner in req_owners])
        queue.dequeue(0)
        assert queue == RegAccessQueue(
            [AccessGroup(AccessType.READ, [owner]) for owner in rem_owners])


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
