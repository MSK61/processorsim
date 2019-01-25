# -*- coding: utf-8 -*-

"""container utilities"""

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
# file:         container_utils.py
#
# function:     generic container utilities
#
# description:  contains helper container functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#
# notes:        This is a private program.
#
############################################################

import itertools


def contains(container, elems):
    """Test the membership of all elements within a container.

    `container` is the container to check elements against.
    `elems` are the elements to check.

    """
    return all(itertools.imap(lambda cur_elem: cur_elem in container, elems))
