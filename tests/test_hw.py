#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests hardware loading service"""

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
# file:         test_hw.py
#
# function:     hardware loading service tests
#
# description:  tests hardware loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.107.1, python 3.14.2, Fedora
#               release 43 (Forty Three)
#
# notes:        This is a private program.
#
############################################################

import os.path
import unittest.mock
from unittest.mock import patch

from attr import frozen
import pytest

import test_utils
import hw_loading
import processor_utils
from processor_utils import units


@frozen
class _TestExpResults:
    """Hardware loading test expected results"""

    raw_isa: object

    proc_srvc_cap: object


@frozen
class _TestInParams:
    """Hardware loading test input parameters"""

    capability: object

    instr: object

    hw_file: object


_HW_CASES = [
    (
        _TestInParams("ALU", "ADD", "processorWithALUISA.yaml"),
        _TestExpResults(("ADD", "ALU"), "ALU"),
    ),
    (
        _TestInParams("MEM", "LW", "processorWithMemISA.yaml"),
        _TestExpResults(("LW", "MEM"), "MEM"),
    ),
]


class TestHwDescLoad:
    """Test case for loading complete hardware description files"""

    @pytest.mark.parametrize("in_params, exp_results", _HW_CASES)
    def test_hw_load_calls_into_processor_and_isa_load_functions(
        self, in_params, exp_results
    ):
        """Test loading a full hardware description file.

        `self` is this test case.
        `in_params` are the test input parameters.
        `exp_results` are the test expected results.
        The method tests appropriate calls are made to load the
        processor and ISA descriptions.

        """
        lock_info = units.LockInfo(True, True)
        with (
            open(
                os.path.join(
                    test_utils.TEST_DATA_DIR, "fullHwDesc", in_params.hw_file
                ),
                encoding="utf-8",
            ) as hw_src,
            patch(
                "processor_utils.load_proc_desc",
                return_value=processor_utils.ProcessorDesc(
                    [],
                    [],
                    [
                        units.UnitModel(
                            "full system",
                            1,
                            [in_params.capability],
                            lock_info,
                            [],
                        )
                    ],
                    [],
                ),
            ) as proc_mock,
            patch(
                "processor_utils.get_abilities",
                return_value=frozenset([in_params.capability]),
            ) as ability_mock,
            patch(
                "processor_utils.load_isa",
                return_value={in_params.instr: in_params.capability},
            ) as isa_mock,
        ):
            assert hw_loading.read_processor(hw_src) == hw_loading.HwDesc(
                proc_mock.return_value, isa_mock.return_value
            )
        isa_mock.assert_called()
        assert tuple(isa_mock.call_args.args[0]) == (exp_results.raw_isa,)
        assert isa_mock.call_args.args[1] == ability_mock.return_value
        mock_checks = _get_checks(
            proc_mock, ability_mock, exp_results.proc_srvc_cap
        )

        for mock_chk in mock_checks:
            unittest.mock.MagicMock.assert_called_with(*mock_chk)


def _get_checks(proc_mock, ability_mock, capability):
    """Create the list of mock checks.

    `proc_mock` is the processor loading mock.
    `ability_mock` is the mock for retrieving abilities.
    `capability` is the hardware sole capability.

    """
    return [
        [
            proc_mock,
            {
                "units": [
                    {
                        units.UNIT_NAME_KEY: "full system",
                        units.UNIT_WIDTH_KEY: 1,
                        units.UNIT_CAPS_KEY: [capability],
                        units.UNIT_RLOCK_KEY: True,
                        units.UNIT_WLOCK_KEY: True,
                    }
                ],
                "dataPath": [],
            },
        ],
        [ability_mock, proc_mock.return_value],
    ]


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
