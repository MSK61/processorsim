#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading memory ACL"""

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
# file:         test_mem_acl.py
#
# function:     memory ACL loading tests
#
# description:  tests loading memory ACL
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.107.1, python 3.14.2, Fedora
#               release 43 (Forty Three)
#
# notes:        This is a private program.
#
############################################################

from logging import WARNING

import pytest
from attr import frozen
from pytest import mark
from test_utils import chk_warnings

from processor_utils import ProcessorDesc, load_proc_desc
from processor_utils.units import (
    UNIT_CAPS_KEY,
    UNIT_MEM_KEY,
    UNIT_NAME_KEY,
    UNIT_RLOCK_KEY,
    UNIT_WIDTH_KEY,
    UNIT_WLOCK_KEY,
    LockInfo,
    UnitModel,
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
            UnitModel(name, 1, ["ALU"], LockInfo(True, True), capabilities)
            for name, capabilities in [(loaded_core, []), ("core 2", ["ALU"])]
        )
        assert load_proc_desc(
            {
                "units": [
                    {
                        UNIT_NAME_KEY: name,
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                        **mem_access,
                    }
                    for name, mem_access in [
                        (ref_cap_unit, {}),
                        ("core 2", {UNIT_MEM_KEY: ["alu"]}),
                    ]
                ],
                "dataPath": [],
            }
        ) == ProcessorDesc([], [], in_out_units, [])
        chk_warnings(["alu", "core 2", "ALU", loaded_core], caplog.records)


class TestPartialMem:
    """Test case for partial memory access"""

    def test_partial_mem_access(self):
        """Test loading a processor with partial memory access.

        `self` is this test case.

        """
        assert load_proc_desc(
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
        ) == ProcessorDesc(
            [],
            [],
            [
                UnitModel(
                    "full system",
                    1,
                    ["ALU", "MEM"],
                    LockInfo(True, True),
                    ["MEM"],
                )
            ],
            [],
        )


@frozen
class _TestExpResults:
    """Non-standard capability loading test expected results"""

    unit: object

    ref_cap: object


@frozen
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
                    exp_results.unit,
                    1,
                    [exp_ref_cap],
                    LockInfo(True, True),
                    [exp_ref_cap],
                )
            ],
            [],
        )
        chk_warnings(
            [exp_ref_cap, exp_results.unit, exp_ref_cap], caplog.records
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
