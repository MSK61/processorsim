#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading units"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025 Mohammed El-Afifi
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
# file:         test_units.py
#
# function:     unit loading tests
#
# description:  tests loading units
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

from fastcore import basics
import pytest

import test_utils
import processor_utils
from processor_utils import ProcessorDesc, units
from processor_utils.units import FuncUnit, LockInfo, UnitModel


class TestDupName:
    """Test case for loading units with duplicate names"""

    @pytest.mark.parametrize(
        "in_file, dup_unit",
        [
            ("twoUnitsWithSameNameAndCase.yaml", "full system"),
            ("twoUnitsWithSameNameAndDifferentCase.yaml", "FULL SYSTEM"),
        ],
    )
    # pylint: disable-next=invalid-name
    def test_two_units_with_same_name_raise_DupElemError(
        self, in_file, dup_unit
    ):
        """Test loading two units with the same name.

        `self` is this test case.
        `in_file` is the processor description file.
        `dup_unit` is the duplicate unit.

        """
        with pytest.raises(processor_utils.exception.DupElemError) as ex_chk:
            test_utils.read_proc_file("units", in_file)
        chk_points = (
            test_utils.ValInStrCheck(elem_getter(ex_chk.value), unit)
            for elem_getter, unit in [
                (basics.Self.new_element(), dup_unit),
                (basics.Self.old_element(), "full system"),
            ]
        )
        test_utils.chk_error(chk_points, ex_chk.value)


class TestExpAttr:
    """Test case for loading units with explicit attributes"""

    def test_processor_with_explicit_attributes(self):
        """Test loading a processor with explicitly defined attributes.

        `self` is this test case.

        """
        assert processor_utils.load_proc_desc(
            {
                "units": [
                    {
                        units.UNIT_NAME_KEY: "full system",
                        units.UNIT_WIDTH_KEY: 1,
                        units.UNIT_CAPS_KEY: ["ALU"],
                        **{
                            attr: True
                            for attr in [
                                units.UNIT_RLOCK_KEY,
                                units.UNIT_WLOCK_KEY,
                            ]
                        },
                        units.UNIT_MEM_KEY: ["ALU"],
                    }
                ],
                "dataPath": [],
            }
        ) == ProcessorDesc(
            [],
            [],
            [
                UnitModel(
                    "full system", 1, ["ALU"], LockInfo(True, True), ["ALU"]
                )
            ],
            [],
        )


class TestPostOrder:
    """Test case for putting units in post-order"""

    def test_processor_puts_units_in_post_order(self):
        """Test putting units in post-order.

        `self` is this test case.

        """
        in_unit, mid1_unit, mid2_unit, mid3_unit, out_unit = (
            UnitModel(name, 1, ["ALU"], LockInfo(rd_lock, wr_lock), [])
            for name, rd_lock, wr_lock in [
                ("input", True, False),
                ("middle 1", False, False),
                ("middle 2", False, False),
                ("middle 3", False, False),
                ("output", False, True),
            ]
        )
        assert ProcessorDesc(
            [in_unit],
            [FuncUnit(out_unit, [mid3_unit])],
            [],
            (
                FuncUnit(model, [pred])
                for model, pred in [
                    (mid1_unit, in_unit),
                    (mid3_unit, mid2_unit),
                    (mid2_unit, mid1_unit),
                ]
            ),
        ).internal_units == tuple(
            FuncUnit(model, [pred])
            for model, pred in [
                (mid3_unit, mid2_unit),
                (mid2_unit, mid1_unit),
                (mid1_unit, in_unit),
            ]
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
