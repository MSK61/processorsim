#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests hardware loading service"""

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
# file:         test_hw.py
#
# function:     hardware loading service tests
#
# description:  tests hardware loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.52.1, python 3.8.7, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

import os.path
import unittest.mock
from unittest.mock import patch

import pytest

import test_utils
import hw_loading
import processor_utils
from processor_utils import units
from str_utils import ICaseString


class TestHwDescLoad:

    """Test case for loading complete hardware description files"""

    @pytest.mark.parametrize("capability, instr, hw_file",
                             [("ALU", "ADD", "processorWithALUISA.yaml"),
                              ("MEM", "LW", "processorWithMemISA.yaml")])
    def test_hw_load_calls_into_processor_and_isa_load_functions(
            self, capability, instr, hw_file):
        """Test loading a full hardware description file.

        `self` is this test case.
        `capability` is the hardware sole capability.
        `instr` is the sole supported instruction.
        `hw_file` is the hardware description file.
        The method tests appropriate calls are made to load the
        processor and ISA descriptions.

        """
        full_sys_unit = ICaseString("fullSys")
        icase_cap = ICaseString(capability)
        lock_info = units.LockInfo(True, True)
        with open(os.path.join(
                test_utils.TEST_DATA_DIR, "fullHwDesc",
                hw_file)) as hw_src, patch(
                    "processor_utils.load_proc_desc",
                    return_value=processor_utils.ProcessorDesc(
                        [], [], [units.UnitModel(
                            full_sys_unit, 1, [icase_cap], lock_info, [])],
                        [])) as proc_mock, patch(
                            "processor_utils.get_abilities",
                            return_value=frozenset(
                                [icase_cap])) as ability_mock, patch(
                                    "processor_utils.load_isa",
                                    return_value={
                                        instr: icase_cap}) as isa_mock:
            assert hw_loading.read_processor(hw_src) == hw_loading.HwDesc(
                proc_mock.return_value, isa_mock.return_value)
        isa_mock.assert_called()
        assert tuple(isa_mock.call_args.args[0]) == ((instr, capability),)
        assert isa_mock.call_args.args[1] == ability_mock.return_value

        for mock_chk in [
                [proc_mock,
                 {"units":
                  [{units.UNIT_NAME_KEY: "fullSys", units.UNIT_WIDTH_KEY: 1,
                    units.UNIT_CAPS_KEY: [capability],
                    units.UNIT_RLOCK_KEY: True, units.UNIT_WLOCK_KEY: True}],
                  "dataPath": []}], [ability_mock, proc_mock.return_value]]:
            unittest.mock.MagicMock.assert_called_with(*mock_chk)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
