#!/usr/bin/env python
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
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 26 (Twenty Six)
#               Komodo IDE, version 11.1.1 build 91089, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
#
# notes:        This is a private program.
#
############################################################

from mock import patch
import os.path
import pytest
import test_utils
import processor
from processor import HwDesc
from processor_utils import ProcessorDesc
import processor_utils.units
from processor_utils.units import UnitModel
from str_utils import ICaseString
import unittest


class CoverageTest(unittest.TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_HwDesc_ne_operator(self):
        """Test HwDesc != operator.

        `self` is this test case.

        """
        empty_str = ICaseString("")
        assert HwDesc(ProcessorDesc([], [], [], []), {}) != HwDesc(
            ProcessorDesc([UnitModel(empty_str, 1, [empty_str])], [], [], []),
            {})

    def test_HwDesc_repr(self):
        """Test HwDesc representation.

        `self` is this test case.

        """
        in_port = UnitModel(ICaseString(""), 1, [ICaseString("")])
        out_port = processor_utils.units.FuncUnit(
            UnitModel(ICaseString("output"), 1, [ICaseString("")]), [in_port])
        repr(HwDesc(ProcessorDesc([in_port], [out_port], [], []), {}))


class _MockCheck:

    """Test case for checking mock calls"""

    def __init__(self, mock_obj, params):
        """Set the mock check information.

        `self` is this mock check.
        `mock_obj` is the mock object.
        `params` are the call parameters.

        """
        self._mock = mock_obj
        self._params = params

    def assert_call(self):
        """Verify the mock call parameters.

        `self` is this mock check.

        """
        self._mock.assert_called_with(*(self._params))


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
        with open(os.path.join(test_utils.TEST_DATA_DIR, "fullHwDesc",
                               hw_file)) as hw_file, patch(
            "processor_utils.load_proc_desc",
            return_value=ProcessorDesc([], [], [UnitModel(
                full_sys_unit, 1, [icase_cap])], [])) as proc_mock, patch(
            "processor_utils.get_abilities",
            return_value=frozenset([icase_cap])) as ability_mock, patch(
            "processor_utils.load_isa",
                return_value={instr: icase_cap}) as isa_mock:
            assert processor.read_processor(hw_file) == HwDesc(
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
