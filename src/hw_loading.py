# -*- coding: utf-8 -*-

"""hardware loading services"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021 Mohammed El-Afifi
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
# file:         hw_loading.py
#
# function:     hardware loading services
#
# description:  loads processor description files
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.54.3, python 3.8.7, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

import copy
import typing
from typing import Any, Iterable, MutableMapping

import attr
import yaml

import processor_utils
from processor_utils.units import UNIT_CAPS_KEY, UNIT_MEM_KEY


def make_unit_dict(new_unit_dict: MutableMapping[
        object, Iterable[Any]]) -> MutableMapping[object, Iterable[Any]]:
    """Create the unit dictionary.

    `new_unit_dict` is the unit dictionary in the new format.
    The function converts the unit dictionary from the new format to the
    old one.

    """
    old_unit_dict = copy.deepcopy(new_unit_dict)
    old_caps = [cap["name"] for cap in old_unit_dict[
        UNIT_CAPS_KEY] if cap.get("memoryAccess", False)]

    if old_caps:
        old_unit_dict[UNIT_MEM_KEY] = old_caps

    old_unit_dict[UNIT_CAPS_KEY] = [
        cap["name"] for cap in old_unit_dict[UNIT_CAPS_KEY]]
    return old_unit_dict


@attr.s(auto_attribs=True, frozen=True)
class HwDesc:

    """Hardware description"""

    processor: processor_utils.ProcessorDesc

    isa: typing.Mapping[str, object]


def read_processor(proc_file: typing.IO[str]) -> HwDesc:
    """Read the processor description from the given file.

    `proc_file` is the YAML file containing the processor description.
    The function constructs necessary processing structures from the
    given processor description file. It returns a processor
    description.

    """
    yaml_desc = yaml.safe_load(proc_file)
    microarch_key = "microarch"
    processor = processor_utils.load_proc_desc(yaml_desc[microarch_key])
    isa_key = "ISA"
    return HwDesc(processor, processor_utils.load_isa(
        yaml_desc[isa_key].items(), processor_utils.get_abilities(processor)))
