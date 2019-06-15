#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""container utilities tests"""

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
# file:         test_containers.py
#
# function:     container utilities tests
#
# description:  tests container auxiliary classes and functions
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
from container_utils import BagValDict
import unittest


class CoverageTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_BagValDict_ne_operator(self):
        """Test BagValDict != operator.

        `self` is this test case.

        """
        assert BagValDict() != BagValDict({test_env.TEST_DIR: [0]})

    def test_BagValDict_repr(self):
        """Test BagValDict representation.

        `self` is this test case.

        """
        repr(BagValDict())


def main():
    """entry point for running test in this module"""
    unittest.main()


if __name__ == '__main__':
    main()
