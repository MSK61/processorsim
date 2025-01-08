#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests capability analysis utilities"""

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
# file:         test_cap_anal.py
#
# function:     capability analysis utilities tests
#
# description:  tests capability analysis utilities
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

import networkx
import pytest

import processor_utils.cap_anal_utils


class TestSplit:
    """Test case for splitting capability graphs"""

    def test_new_unit_is_larger_than_the_original_by_the_graph_size(self):
        """Test splitting a graph.

        `self` is this test case.

        """
        graph = networkx.DiGraph({0: [2, 3], 1: [4, 5]})

        for in_node in [0, 1]:
            graph.nodes[in_node][processor_utils.units.UNIT_WIDTH_KEY] = 1

        assert processor_utils.cap_anal_utils.split_nodes(graph)[1] == 7


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
