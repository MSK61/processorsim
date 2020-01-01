#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor sanity checks"""

############################################################
#
# Copyright 2017, 2019, 2020 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.41.1, python 3.7.5, Fedora release
#               31 (Thirty One)
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
import container_utils
from container_utils import concat_dicts
from processor_utils import exception, load_proc_desc
from processor_utils.exception import MultilockError
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


class WidthTest(unittest.TestCase):

    """Test case for checking data path width"""

    # pylint: disable=invalid-name
    def test_unconsumed_capabilitiy_raises_BlockedCapError(self):
        """Test an input with a capability not consumed at all.

        `self` is this test case.

        """
        with self.assertRaises(exception.BlockedCapError) as ex_chk:
            read_proc_file("widths", "inputPortWithUnconsumedCapability.yaml")
        chk_error([ValInStrCheck(
            "Capability " + ex_chk.exception.capability, "Capability MEM"),
                   ValInStrCheck("port " + ex_chk.exception.port,
                                 "port input")], ex_chk.exception)


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
        both_locks = map(
            lambda lock_prop: (lock_prop, True), ["readLock", "writeLock"])
        load_proc_desc(
            {"units":
             [{"name": "ALU input", "width": 1, "capabilities": ["ALU"],
               "readLock": True},
              {"name": "MEM input", "width": 1, "capabilities": ["MEM"]},
              {"name": "center", "width": 1, "capabilities": ["ALU", "MEM"]},
              {"name": "ALU output", "width": 1, "capabilities": ["ALU"],
               "writeLock": True},
              concat_dicts({"name": "MEM output", "width": 1,
                            "capabilities": ["MEM"]}, dict(both_locks))],
             "dataPath": [["ALU input", "center"], ["MEM input", "center"], [
                 "center", "ALU output"], ["center", "MEM output"]]})

    # pylint: disable=invalid-name
    @mark.parametrize("proc_desc, lock_data", [
        (_IoProcessor("input", "output", "ALU"), _LockTestData(
            "readLock", "read")), (_IoProcessor("in_unit", "out_unit", "MEM"),
                                   _LockTestData("writeLock", "write"))])
    def test_path_with_multiple_locks_raises_MultilockError(
            self, proc_desc, lock_data):
        """Test loading a processor with multiple locks in paths.

        `self` is this test case.
        `proc_desc` is the processor description.
        `lock_data` is the lock test data.

        """
        in_locks = map(lambda lock_prop: (lock_prop, True),
                       ["readLock", lock_data.prop_name])
        out_locks = map(lambda lock_prop: (lock_prop, True),
                        ["writeLock", lock_data.prop_name])
        ex_info = raises(
            MultilockError, load_proc_desc,
            {"units": [concat_dicts(
                {"name": proc_desc.in_unit, "width": 1, "capabilities":
                 [proc_desc.capability]}, dict(in_locks)), concat_dicts(
                     {"name": proc_desc.out_unit, "width": 1, "capabilities": [
                         proc_desc.capability]}, dict(out_locks))],
             "dataPath": [[proc_desc.in_unit, proc_desc.out_unit]]})
        assert ex_info.value.start == ICaseString(proc_desc.in_unit)
        assert ex_info.value.lock_type == lock_data.lock_type
        assert ex_info.value.capability == ICaseString(proc_desc.capability)
        assert container_utils.contains(str(ex_info.value), [
            lock_data.lock_type, proc_desc.capability, proc_desc.in_unit])

    @mark.parametrize("units, data_path", [
        ([{"name": "input", "width": 1, "capabilities": ["ALU"], "writeLock":
           True}, {"name": "output 1", "width": 1, "capabilities": ["ALU"]},
          {"name": "output 2", "width": 1, "capabilities": ["ALU"],
           "readLock": True}], [["input", "output 1"], ["input", "output 2"]]),
        ([{"name": "fullSys", "width": 1, "capabilities": ["ALU"],
           "writeLock": True}], [])])
    def test_path_with_no_locks_raises_MultilockError(self, units, data_path):
        """Test loading a processor with no locks in paths.

        `self` is this test case.
        `units` are the processor units.
        `data_path` is the data path between units.

        """
        raises(MultilockError, load_proc_desc,
               {"units": units, "dataPath": data_path})


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
