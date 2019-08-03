#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests hardware loading service"""

############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
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
# environment:  Komodo IDE, version 11.1.1 build 91089, python 3.7.3,
#               Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import mock
from mock import patch
import os.path
import pytest
import test_utils
import processor
import processor_utils
from processor_utils import units
from str_utils import ICaseString
import typing


class _MockCheck(typing.NamedTuple):

    """Test case for checking mock calls"""

    def assert_call(self):
        """Verify the mock call parameters.

        `self` is this mock check.

        """
        self.mock_obj.assert_called_with(*self.params)

    mock_obj: mock.MagicMock

    params: typing.Iterable


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
        lock_info = units.LockInfo(False, False)
        with open(os.path.join(test_utils.TEST_DATA_DIR, "fullHwDesc",
                               hw_file)) as hw_file, patch(
            "processor_utils.load_proc_desc",
            return_value=processor_utils.ProcessorDesc(
                [], [], [units.UnitModel(full_sys_unit, 1, [icase_cap],
                                         lock_info)], [])) as proc_mock, patch(
            "processor_utils.get_abilities",
            return_value=frozenset([icase_cap])) as ability_mock, patch(
            "processor_utils.load_isa",
                return_value={instr: icase_cap}) as isa_mock:
            assert processor.read_processor(hw_file) == processor.HwDesc(
                proc_mock.return_value, isa_mock.return_value)

        for mock_chk in [
            _MockCheck(proc_mock, [
                {"units": [{"name": "fullSys", "width": 1,
                            "capabilities": [capability]}], "dataPath": []}]),
            _MockCheck(ability_mock, [proc_mock.return_value]), _MockCheck(
                isa_mock, [{instr: capability}, ability_mock.return_value])]:
            mock_chk.assert_call()


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
