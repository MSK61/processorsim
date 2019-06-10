#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests registry access structures"""

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
# function:     registry access plan tests
#
# description:  tests registry access plan creation
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import test_env
from reg_access import RegAccessQueue
import unittest
from unittest import TestCase


class AccessPlanTest(TestCase):

    """Test case for creating registry access plans"""

    def test_adding_read_to_empty_queue_creates_a_new_read(self):
        """Test adding a read request to an empty queue.

        `self` is this test case.

        """
        plan = RegAccessQueue()
        plan.add_read(0)
        assert plan == RegAccessQueue([0])


class CoverageTest(TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_RegAccessQueue_ne_operator(self):
        """Test RegAccessQueue != operator.

        `self` is this test case.

        """
        assert RegAccessQueue() != RegAccessQueue([0])

    def test_RegAccessQueue_repr(self):
        """Test RegAccessQueue representation.

        `self` is this test case.

        """
        repr(RegAccessQueue([0]))


def main():
    """entry point for running test in this module"""
    unittest.main()

if __name__ == '__main__':
    main()

test_env.TEST_DIR
