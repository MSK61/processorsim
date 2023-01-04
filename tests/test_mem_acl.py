#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading edges"""

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
# file:         test_mem_acl.py
#
# function:     memory ACL loading tests
#
# description:  tests loading memory ACL
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.74.2, python 3.11.1, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################

from logging import WARNING
import unittest

import attr
import pytest
from pytest import mark

from processor_utils import load_proc_desc, ProcessorDesc
from processor_utils.units import (
    LockInfo,
    UNIT_CAPS_KEY,
    UNIT_MEM_KEY,
    UnitModel,
    UNIT_NAME_KEY,
    UNIT_RLOCK_KEY,
    UNIT_WIDTH_KEY,
    UNIT_WLOCK_KEY,
)
from str_utils import ICaseString


class PartialMemTest(unittest.TestCase):

    """Test case for partial memory access"""

    def test_partial_mem_access(self):
        """Test loading a processor with partial memory access.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(
            ICaseString("full system"),
            1,
            {
                ICaseString(name): mem_access
                for name, mem_access in [("ALU", False), ("MEM", True)]
            },
            LockInfo(True, True),
        )
        self.assertEqual(
            load_proc_desc(
                {
                    "units": [
                        {
                            UNIT_NAME_KEY: "full system",
                            UNIT_WIDTH_KEY: 1,
                            UNIT_CAPS_KEY: ["ALU", "MEM"],
                            **{
                                attr: True
                                for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                            },
                            UNIT_MEM_KEY: ["MEM"],
                        }
                    ],
                    "dataPath": [],
                }
            ),
            ProcessorDesc([], [], [full_sys_unit], []),
        )


class TestCapCase:

    """Test case for checking ACL capability cases"""

    @mark.parametrize(
        "ref_cap_unit, loaded_core",
        [("core 1", "core 1"), ("core 0", "core 0")],
    )
    def test_capability_case_is_checked_across_all_units(
        self, caplog, ref_cap_unit, loaded_core
    ):
        """Test ACL capability cases are checked across all units.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `ref_cap_unit` is the unit containing the reference capability
                       name.
        `loaded_core` is the loaded core unit name.

        """
        caplog.set_level(WARNING)
        in_out_units = (
            UnitModel(
                ICaseString(name),
                1,
                {ICaseString("ALU"): mem_access},
                LockInfo(True, True),
            )
            for name, mem_access in [(loaded_core, False), ("core 2", True)]
        )
        assert load_proc_desc(
            {
                "units": [
                    {
                        UNIT_NAME_KEY: ref_cap_unit,
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                    },
                    {
                        UNIT_NAME_KEY: "core 2",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                        UNIT_MEM_KEY: ["alu"],
                    },
                ],
                "dataPath": [],
            }
        ) == ProcessorDesc([], [], in_out_units, [])
        assert caplog.records
        warn_msg = caplog.records[0].getMessage()

        for token in ["alu", "core 2", "ALU", loaded_core]:
            assert token in warn_msg


@attr.s(auto_attribs=True, frozen=True)
class _TestExpResults:

    """Non-standard capability loading test expected results"""

    unit: object

    ref_cap: object


@attr.s(auto_attribs=True, frozen=True)
class _TestInParams:

    """Non-standard capability loading test input results"""

    core_unit: object

    ref_cap: object


_STD_CAP_CASES = [
    (
        _TestInParams("full system", "alu"),
        _TestExpResults("full system", "alu"),
    ),
    (
        _TestInParams("single core", "alu"),
        _TestExpResults("single core", "alu"),
    ),
    (
        _TestInParams("full system", "Alu"),
        _TestExpResults("full system", "Alu"),
    ),
    (
        _TestInParams("full system", "mem"),
        _TestExpResults("full system", "mem"),
    ),
]


class TestStdCaseCap:

    """Test case for loading a non-standard capability case"""

    @mark.parametrize("in_params, exp_results", _STD_CAP_CASES)
    def test_capability_with_nonstandard_case_is_detected(
        self, caplog, in_params, exp_results
    ):
        """Test loading an ACL with a non-standard capability case.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `in_params` are the test input parameters.
        `exp_results` are the test expected results.

        """
        caplog.set_level(WARNING)
        exp_ref_cap = exp_results.ref_cap.upper()
        assert load_proc_desc(
            {
                "units": [
                    {
                        UNIT_NAME_KEY: in_params.core_unit,
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: [in_params.ref_cap.upper()],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                        UNIT_MEM_KEY: [in_params.ref_cap],
                    }
                ],
                "dataPath": [],
            }
        ) == ProcessorDesc(
            [],
            [],
            [
                UnitModel(
                    ICaseString(exp_results.unit),
                    1,
                    {ICaseString(exp_ref_cap): True},
                    LockInfo(True, True),
                )
            ],
            [],
        )
        assert caplog.records
        warn_msg = caplog.records[0].getMessage()

        for token in [exp_ref_cap, exp_results.unit, exp_ref_cap]:
            assert token in warn_msg


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
