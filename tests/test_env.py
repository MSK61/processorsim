# -*- coding: utf-8 -*-

"""test environment setup"""

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
# file:         test_env.py
#
# function:     test environment initialization
#
# description:  initializes logging and prepares for importing source
#               modules inside the test environment
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.36.1, python 3.7.3, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import logging
import os
import sys
TEST_DIR = os.path.dirname(__file__)


def _add_src_path():
    """Add the source path to the python search path.

    The function prepares the test environment so that source modules
    may be imported in test modules.

    """
    src_dir = "src"
    sys.path.append(os.path.join(TEST_DIR, os.pardir, src_dir))


def _init():
    """Initialize the test environment."""
    _add_src_path()
    logging.basicConfig(level=logging.INFO)


_init()
