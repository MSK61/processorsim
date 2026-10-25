#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading memory ACL"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
# Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.143.1, python 3.14.8, Fedora
#               release 44 (Forty Four)
#
# notes:        This is a private program.
#
############################################################

import pytest

import processor_utils
from processor_utils import units


class TestPartialMem:
    """Test case for partial memory access"""

    def test_partial_mem_access(self):
        """Test loading a processor with partial memory access.

        `self` is this test case.

        """
        assert processor_utils.load_proc_desc(
            {
                "units": [
                    {
                        units.UNIT_NAME_KEY: "full system",
                        units.UNIT_WIDTH_KEY: 1,
                        units.UNIT_ROLES_KEY: [
                            {
                                units.ROLE_NAME_KEY: name,
                                units.ROLE_MEM_KEY: uses_mem,
                            }
                            for name, uses_mem in [
                                ("ALU", False),
                                ("MEM", True),
                            ]
                        ],
                        **{
                            attr: True
                            for attr in [
                                units.UNIT_RLOCK_KEY,
                                units.UNIT_WLOCK_KEY,
                            ]
                        },
                    }
                ],
                "dataPath": [],
            }
        ) == processor_utils.ProcessorDesc(
            [],
            [],
            [
                units.UnitModel(
                    "full system",
                    1,
                    {"ALU": False, "MEM": True},
                    units.LockInfo(True, True),
                )
            ],
            [],
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
