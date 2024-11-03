# -*- coding: utf-8 -*-

"""wrappers for appeasing type checkers"""

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
# file:         type_checking.py
#
# function:     type checking clutches
#
# description:  contains wrappers for services that might upset type
#               checkers
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.95.1, python 3.12.7, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import collections.abc
import typing
from typing import Any

import fastcore.basics

_T = typing.TypeVar("_T")


def call(func: collections.abc.Callable[..., _T], *args: object) -> _T:
    """Call the given functor with arguments.

    `func` is the function to call.
    `args` are the arguments to call the function with.
    This function is used whenever pylance can't match arguments with
    the inferred types of parameters.

    """
    return func(*args)


def map_ex(seq: Any, map_func: Any, _: type[_T]) -> "map[_T]":
    """Map an iterable using a mapping function.

    `seq` is the iterable to map.
    `map_func` is the mapping function.
    `_` is the type of elements in the resulting mapped generator.
    I'm casting to map[_T] due to a missing explicit type hint for the
    return type of the fastcore.basics.map_ex function.

    """
    return typing.cast(
        "map[_T]", fastcore.basics.map_ex(seq, map_func, gen=True)
    )
