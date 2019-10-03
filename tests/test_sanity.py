#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests processor sanity checks"""

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
# file:         test_sanity.py
#
# function:     tests for processor sanity checks during loading
#
# description:  tests processor sanity checks
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.38.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import unittest

import attr
import networkx
import pytest
from pytest import mark, raises

from test_utils import chk_error, read_proc_file, ValInStrCheck
from processor_utils import exception, load_proc_desc
from str_utils import ICaseString


class TestBlocking:

    """Test case for detecting blocked inputs"""

    # pylint: disable=invalid-name
    @mark.parametrize(
        "in_file, isolated_input", [("isolatedInputPort.yaml", "input 2"), (
            "processorWithNoCapableOutputs.yaml", "input")])
    def test_in_port_with_no_compatible_out_links_raises_DeadInputError(
            self, in_file, isolated_input):
        """Test an input port with only incompatible out links.

        `self` is this test case.
        `in_file` is the processor description file.
        `isolated_input` is the input unit that gets isolated during
                         optimization.
        An incompatible link is a link connecting an input port to a
        successor unit with no capabilities in common.

        """
        ex_chk = raises(
            exception.DeadInputError, read_proc_file, "blocking", in_file)
        chk_error([ValInStrCheck(
            ex_chk.value.port, ICaseString(isolated_input))], ex_chk.value)
    # pylint: enable=invalid-name


class TestLoop:

    """Test case for loading processors with loops"""

    # pylint: disable=invalid-name
    @mark.parametrize("in_file", [
        "selfNodeProcessor.yaml", "bidirectionalEdgeProcessor.yaml",
        "bigLoopProcessor.yaml"])
    def test_loop_raises_NetworkXUnfeasible(self, in_file):
        """Test loading a processor with a loop.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        raises(networkx.NetworkXUnfeasible, read_proc_file, "loops", in_file)
    # pylint: enable=invalid-name


class WidthTest(unittest.TestCase):

    """Test case for checking data path width"""

    # pylint: disable=invalid-name
    def test_unconsumed_capabilitiy_raises_BlockedCapError(self):
        """Test an input with a capability not consumed at all.

        `self` is this test case.

        """
        ex_chk = raises(exception.BlockedCapError, read_proc_file, "widths",
                        "inputPortWithUnconsumedCapability.yaml")
        chk_error([ValInStrCheck(
            "Capability " + ex_chk.value.capability, "Capability MEM"),
                   ValInStrCheck("port " + ex_chk.value.port, "port input")],
                  ex_chk.value)
    # pylint: enable=invalid-name


@attr.s(auto_attribs=True, frozen=True)
class _IoProcessor:

    """Single input, single output processor"""

    in_unit: str

    out_unit: str

    capability: str


@attr.s(auto_attribs=True, frozen=True)
class _LockTestData:

    """Lock test data"""

    prop_name: str

    lock_type: str


class TestLocks:

    """Test case for checking processors for path locks"""

    def test_paths_with_multiple_locks_are_only_detected_per_capability(self):
        """Test detecting multi-lock paths per capability.

        `self` is this test case.
        The method asserts that multiple locks across a path with different
        capabilities don't raise an exception as long as single-capability
        paths don't have multiple locks.

        """
        load_proc_desc({"units": [
            {"name": "ALU input", "width": 1, "capabilities": ["ALU"],
             "readLock": True},
            {"name": "MEM input", "width": 1, "capabilities": ["MEM"]},
            {"name": "center", "width": 1, "capabilities": ["ALU", "MEM"]},
            {"name": "ALU output", "width": 1, "capabilities": ["ALU"]},
            {"name": "MEM output", "width": 1, "capabilities": ["MEM"],
             "readLock": True}], "dataPath": [
                 ["ALU input", "center"], ["MEM input", "center"],
                 ["center", "ALU output"], ["center", "MEM output"]]})

    # pylint: disable=invalid-name
    @mark.parametrize("proc_desc, lock_data", [
        (_IoProcessor("input", "output", "ALU"),
         _LockTestData("readLock", "read")),
        (_IoProcessor("in_unit", "out_unit", "ALU"),
         _LockTestData("readLock", "read")),
        (_IoProcessor("input", "output", "ALU"),
         _LockTestData("writeLock", "write")),
        (_IoProcessor("input", "output", "MEM"),
         _LockTestData("readLock", "read"))])
    def test_path_with_multiple_locks_raises_MultilockError(
            self, proc_desc, lock_data):
        """Test loading a processor with multiple locks in paths.

        `self` is this test case.
        `proc_desc` is the processor description.
        `lock_data` is the lock test data.

        """
        ex_info = raises(exception.MultilockError, load_proc_desc, {
            "units": [
                {"name": proc_desc.in_unit, "width": 1, "capabilities":
                 [proc_desc.capability], lock_data.prop_name: True},
                {"name": proc_desc.out_unit, "width": 1, "capabilities":
                 [proc_desc.capability], lock_data.prop_name: True}],
            "dataPath": [[proc_desc.in_unit, proc_desc.out_unit]]})
        assert ex_info.value.segment == [ICaseString(unit) for unit in [
            proc_desc.in_unit, proc_desc.out_unit]]
        assert ex_info.value.lock_type == lock_data.lock_type
        ex_str = str(ex_info.value)
        lock_type_idx = ex_str.find(lock_data.lock_type)
        assert lock_type_idx >= 0
        cap_idx = ex_str.find(proc_desc.capability, lock_type_idx + 1)
        assert cap_idx >= 0
        assert ex_str.find(", ".join([proc_desc.in_unit, proc_desc.out_unit]),
                           cap_idx + 1) >= 0
    # pylint: enable=invalid-name


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
