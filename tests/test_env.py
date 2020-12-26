# -*- coding: utf-8 -*-

"""test environment setup"""

############################################################
#
# Copyright 2017, 2019, 2020 Mohammed El-Afifi
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
# file:         test_env.py
#
# function:     test environment initialization
#
# description:  initializes logging and prepares for importing source
#               modules inside the test environment
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.52.1, python 3.8.6, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

import logging
import os.path
import sys

from test_paths import TEST_DIR
__all__ = ["TEST_DIR"]


def _add_src_path():
    """Add the source path to the python search path.

    The function prepares the test environment so that source modules
    may be imported in test modules.

    """
    sys.path.append(os.path.join(TEST_DIR, "../src"))


def _init():
    """Initialize the test environment."""
    _add_src_path()
    logging.basicConfig(level=logging.INFO)


_init()
