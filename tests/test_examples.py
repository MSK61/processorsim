#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""examples execution tests"""

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
# file:         test_examples.py
#
# function:     examples execution tests
#
# description:  makes sure examples don't get outdated
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from os.path import join

import pytest

import test_paths
import test_type_chks


class TestExample:

    """Test case for fulfilling complete code coverage"""

    def test_example(self):
        """Test example execution.

        `self` is this test case.

        """
        examples_dir = join(test_paths.TEST_DIR, "../examples")
        with open(
            join(examples_dir, "unified memory.ipynb"), encoding="utf-8"
        ) as nb_file:
            test_type_chks.exec_file(nb_file, examples_dir)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
