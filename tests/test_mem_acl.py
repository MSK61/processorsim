#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading memory ACL"""

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
# file:         test_mem_acl.py
#
# function:     memory ACL loading tests
#
# description:  tests loading memory ACL
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.94.1, python 3.12.6, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import pytest

from processor_utils import load_proc_desc, ProcessorDesc
from processor_utils.units import (
    LockInfo,
    ROLE_MEM_KEY,
    ROLE_NAME_KEY,
    UnitModel,
    UNIT_NAME_KEY,
    UNIT_RLOCK_KEY,
    UNIT_ROLES_KEY,
    UNIT_WIDTH_KEY,
    UNIT_WLOCK_KEY,
)


class TestCapCase:
    """Test case for checking ACL capability cases"""

    @pytest.mark.parametrize(
        "ref_cap_unit, loaded_core",
        [("core 1", "core 1"), ("core 0", "core 0")],
    )
    def test_capability_case_is_checked_across_all_units(
        self, ref_cap_unit, loaded_core
    ):
        """Test ACL capability cases are checked across all units.

        `self` is this test case.
        `ref_cap_unit` is the unit containing the reference capability
                       name.
        `loaded_core` is the loaded core unit name.

        """
        in_out_units = (
            UnitModel(name, 1, {"ALU": uses_mem}, LockInfo(True, True))
            for name, uses_mem in [(loaded_core, False), ("core 2", True)]
        )
        assert load_proc_desc(
            {
                "units": [
                    {
                        UNIT_NAME_KEY: name,
                        UNIT_WIDTH_KEY: 1,
                        UNIT_ROLES_KEY: [
                            {ROLE_NAME_KEY: "ALU", ROLE_MEM_KEY: uses_mem}
                        ],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                    }
                    for name, uses_mem in [
                        (ref_cap_unit, False),
                        ("core 2", True),
                    ]
                ],
                "dataPath": [],
            }
        ) == ProcessorDesc([], [], in_out_units, [])


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
                        UNIT_ROLES_KEY: [
                            {ROLE_NAME_KEY: name, ROLE_MEM_KEY: uses_mem}
                            for name, uses_mem in [
                                ("ALU", False),
                                ("MEM", True),
                            ]
                        ],
                        **{
                            attr: True
                            for attr in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
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
                    {"ALU": False, "MEM": True},
                    LockInfo(True, True),
                )
            ],
            [],
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
