#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""examples execution tests"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.74.2, python 3.11.1, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################

from os.path import join
import unittest

import nbconvert.preprocessors
import nbformat

import test_paths


class ExampleTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_example(self):
        """Test example execution.

        `self` is this test case.

        """
        examples_dir = join(test_paths.TEST_DIR, "../examples")
        with open(
            join(examples_dir, "unified memory.ipynb"), encoding="utf-8"
        ) as nb_file:
            nbconvert.preprocessors.ExecutePreprocessor().preprocess(
                nbformat.read(nb_file, nbformat.NO_CONVERT),
                {"metadata": {"path": examples_dir}},
            )


def main():
    """entry point for running test in this module"""
    unittest.main()


if __name__ == "__main__":
    main()
