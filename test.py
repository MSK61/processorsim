#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
runs all unit tests

Usage: test.py
"""

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
# file:         test.py
#
# function:     unit test runner
#
# description:  runs all unit tests
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.40.1, python 3.7.5, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import sys

import pytest


def main():
    """Run the program.

    The function returns the program exit code.

    """
    run()
    return 0        # success


def run():
    """Simulate the program on the given processor."""
    pytest.main()


if __name__ == '__main__':
    sys.exit(main())
