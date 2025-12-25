#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""container utilities tests"""

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
# file:         test_containers.py
#
# function:     container utilities tests
#
# description:  tests container auxiliary classes and functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.107.1, python 3.14.2, Fedora
#               release 43 (Forty Three)
#
# notes:        This is a private program.
#
############################################################

import pydash
import pytest
import test_env

import container_utils


class TestCoverage:
    """Test case for fulfilling complete code coverage"""

    def test_BagValDict_hash(self):
        """Test BagValDict hashing.

        `self` is this test case.

        """
        hash(container_utils.BagValDict())

    def test_IndexedSet_repr(self):
        """Test IndexedSet representation.

        `self` is this test case.

        """
        indexed_set = container_utils.IndexedSet[str](pydash.identity)
        indexed_set.add(test_env.TEST_DIR)
        assert repr(indexed_set)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
