# -*- coding: utf-8 -*-

"""source importer"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

import logging
import os
import sys

def _add_src_path():
    """Add the source path to the python search path.

    The function prepares the test environment so that source modules
    may be imported in test modules.

    """
    src_dir = "src"
    sys.path.append(os.path.join(os.path.pardir, src_dir))


def _init():
    """Initialize the test environment."""
    _add_src_path()
    logging.basicConfig(level=logging.INFO)

_init()