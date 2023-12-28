# -*- coding: utf-8 -*-

"""generic exceptions"""

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
# file:         errors.py
#
# function:     generic exceptions
#
# description:  contains generic exception classes
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from collections import abc
import itertools
import string
import typing
from typing import Final

import attr
import fastcore.foundation

# Attrs doesn't honor class variables annotated with typing.Final(albeit
# being mandated by PEP-591) and instead still treats them as instance
# attributes. That's why I'm using auto_attribs=False and marking the
# attributes explicitly.
# __attrs_init__() passes the attributes verbatim to super().__init__()
# when auto_exc is left to its default(True). I'm setting auto_exc=False
# so that I may call super().__init__() with my custom message.
# Looks like mypy can't honor auto_detect=True in attr.frozen so I have
# to explicitly(and redundantly) use init=False.
EXCEPTION: Final = attr.frozen(auto_attribs=False, auto_exc=False, init=False)
_T = typing.TypeVar("_T")


@attr.frozen
class ElementValue:

    """Error element value

    An element value can have two forms: the form stored in memory and
    the one displayed in error messages.

    """

    @classmethod
    def create_simple(cls, val: object) -> "ElementValue":
        """Create an element value.

        `cls` is the element value class.
        `val` is the desired value.
        The method creates an element value that's displayed and stored
        the same way.

        """
        return cls(*(itertools.repeat(val, 2)))

    displayed: object

    stored: object


@attr.frozen
class ErrorElement(typing.Generic[_T]):

    """Error element"""

    key: str

    val: _T


class SimErrorBase(RuntimeError):

    """Simulation exception base class"""

    def _init(
        self, msg_tmpl: str, elems: abc.Collection[ErrorElement[ElementValue]]
    ) -> None:
        """Create a simulation error.

        `self` is this simulation error.
        `msg_tmpl` is the error message format taking the error elements
                   as keyword arguments.
        `elems` are the error elements.

        """
        super().__init__(
            string.Template(msg_tmpl).substitute(
                {elem.key: elem.val.displayed for elem in elems}
            )
        )
        val_extractor = fastcore.foundation.Self.val().stored()
        # Pylance and pylint can't detect __attrs_init__ as an injected
        # method.
        # pylint: disable-next=no-member
        self.__attrs_init__(  # type: ignore[attr-defined]
            *(map(val_extractor, elems))
        )

    def _init_simple(
        self, msg_tmpl: str, elems: abc.Iterable[ErrorElement[object]]
    ) -> None:
        """Initialize a simulation error with simple elements.

        `self` is this simulation error.
        `msg_tmpl` is the error message format taking the error elements
                   as keyword arguments.
        `elems` are the error elements.
        Simple elements are those which are stored and displayed the
        same way.

        """
        self._init(
            msg_tmpl,
            [
                ErrorElement(elem.key, ElementValue.create_simple(elem.val))
                for elem in elems
            ],
        )


@EXCEPTION
class UndefElemError(SimErrorBase):

    """Unknown set element error"""

    def __init__(self, msg_tmpl: str, elem: object) -> None:
        """Create an unknown element error.

        `self` is this unknown element error.
        `msg_tmpl` is the error message format taking the unknown
                   element as a keyword argument.
        `elem` is the unknown element.

        """
        self._init_simple(msg_tmpl, [ErrorElement(self.ELEM_KEY, elem)])

    ELEM_KEY: Final = "elem"  # parameter key in message format

    element: object = attr.field()
