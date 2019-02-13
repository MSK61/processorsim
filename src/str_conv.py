# -*- coding: utf-8 -*-

"""string conversion utilities"""

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
# file:         str_conv.py
#
# function:     generic string conversion utilities
#
# description:  contains helper string conversion functions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 11.1.1 build 91033, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################


def format_obj(cls_name, field_strings):
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `fields` are the string representations of the object fields.

    """
    sep = ", "
    return '{}({})'.format(cls_name, sep.join(field_strings))


def get_obj_repr(cls_name, fields):
    """Construct a string representation for the given object.

    `cls_name` is the class name.
    `fields` are the object fields.

    """
    return format_obj(cls_name, map(repr, fields))
