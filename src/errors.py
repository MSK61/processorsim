# -*- coding: utf-8 -*-

"""generic exceptions"""

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
# file:         errors.py
#
# function:     generic exceptions
#
# description:  contains generic exception classes
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################


class UndefElemError(RuntimeError):

    """Unknown set element error"""

    def __init__(self, msg_tmpl, elem):
        """Create an unknown element error.

        `self` is this unknown element error.
        `msg_tmpl` is the error message format taking the unknown
                   element as a positional argument.
        `elem` is the unknown element.

        """
        RuntimeError.__init__(self, msg_tmpl.format(elem))
        self._elem = elem

    @property
    def element(self):
        """Unknown element

        `self` is this unknown element error.

        """
        return self._elem
