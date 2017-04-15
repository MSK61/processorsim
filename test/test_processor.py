#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor services"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# file:         test_processor.py
#
# function:     processor service tests
#
# description:  tests processor and ISA loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

import itertools
import mock
import networkx
import os.path
import pytest
from pytest import mark, raises
import test_env
import processor_utils
from processor_utils import FuncUnit, ProcessorDesc, UnitModel
import yaml

class TestLoop:

    """Test case for loading processors with loops"""

    @mark.parametrize("in_file", [
        "selfNodeProcessor.yaml", "bidirectionalEdgeProcessor.yaml",
        "bigLoopProcessor.yaml"])
    def test_loop_raises_NetworkXUnfeasible(self, in_file):
        """Test loading a processor with a loop.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        raises(networkx.NetworkXUnfeasible, _read_file, in_file)


class _VerifyPoint:

    """Verification point"""

    def __init__(self, real_val, exp_val):
        """Create a verification point.

        `self` is this verification point.
        `real_val` is the actual value.
        `exp_val` is the expected value.
        The constructor asserts that the real and expected values match.

        """
        assert real_val == exp_val
        self._value = exp_val

    def check(self, error_msg, start_index):
        """Check that the error message contains the associated value.

        `self` is this verification point.
        `error_msg` is the error message to be checked.
        `start_index` is the index to start searching at.
        The method returns the index of the associated value in the
        given error message after the specified index.

        """
        start_index = error_msg.find(str(self._value), start_index + 1)
        assert start_index >= 0
        return start_index


class TestEdges:

    """Test case for loading edges"""

    def test_edge_with_unknown_unit_raises_ElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        exChk = raises(processor_utils.UndefElemError, _read_file,
                       "edgeWithUnknownUnit.yaml")
        _chk_error([_VerifyPoint(exChk.value.element, "input")], exChk.value)

    @mark.parametrize("in_file, bad_edge", [("emptyEdge.yaml", []),
        ("3UnitEdge.yaml", ["input", "middle", "output"])])
    def test_edge_with_wrong_number_of_units_raises_BadEdgeError(
        self, in_file, bad_edge):
        """Test loading an edge with wrong number of units.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_edge` is the bad edge.

        """
        exChk = raises(processor_utils.BadEdgeError, _read_file, in_file)
        _chk_error([_VerifyPoint(exChk.value.edge, bad_edge)], exChk.value)

    @mark.parametrize("in_file, edges",
                      [("twoEdgesWithSameUnitNamesAndCase.yaml",
                        [["input", "output"]]),
                        ("twoEdgesWithSameUnitNamesAndLowerThenUpperCase.yaml",
                         [["input", "output"], ["INPUT", "OUTPUT"]]),
                        ("twoEdgesWithSameUnitNamesAndUpperThenLowerCase.yaml",
                         [["INPUT", "OUTPUT"], ["input", "output"]])])
    def test_two_identical_edges_are_detected(self, in_file, edges):
        """Test loading two identical edges with the same units.

        `self` is this test case.
        `in_file` is the processor description file.
        `edges` are the identical edges.

        """
        with mock.patch("logging.warning") as warn_mock:
            _chk_two_units(_read_file(in_file))
        self._chk_edge_warn(edges, warn_mock)

    @staticmethod
    def _chk_edge_warn(edges, warn_mock):
        """Verify edges in a warning message.

        `edges` are the edges to assess.
        `warn_mock` is the warning function mock.
        The method asserts that all edges exist in the constructed
        warning message.

        """
        assert warn_mock.call_args
        warn_msg = warn_mock.call_args[0][0].format(
            *(warn_mock.call_args[0][1 :]), **(warn_mock.call_args[1]))
        assert all(itertools.imap(lambda edge: str(edge) in warn_msg, edges))


class TestProcessors:

    """Test case for loading valid processors"""

    def test_processor_with_one_two_wide_input_and_two_one_wide_outputs(self):
        """Test loading a processor with an input and two outputs.

        `self` is this test case.

        """
        _read_file("oneInputTwoOutputProcessor.yaml")

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = _read_file("4ConnectedUnitsProcessor.yaml")
        assert not proc_desc.in_out_ports
        internal_unit = UnitModel("middle", 1, [])
        assert (proc_desc.in_ports,
                sorted(proc_desc.out_ports, key=lambda port: port.model.name),
                proc_desc.internal_units) == ((UnitModel("input", 1, []),),
            [FuncUnit(UnitModel("output 1", 1, []), proc_desc.in_ports),
             FuncUnit(UnitModel("output 2", 1, []), [proc_desc.internal_units[
                0].model])], (FuncUnit(internal_unit, proc_desc.in_ports),))

    @mark.parametrize(
        "in_file", ["twoConnectedUnitsProcessor.yaml",
                    "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml"])
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        _chk_two_units(_read_file(in_file))

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        assert _read_file("singleUnitProcessor.yaml") == ProcessorDesc(
            [], [], [UnitModel("fullSys", 1, ["ALU"])], [])


class TestUnits:

    """Test case for loading processor units"""

    def test_empty_processor_raises_EmptyProcError(self):
        """Test a processor with no units.

        `self` is this test case.

        """
        raises(
            processor_utils.EmptyProcError, _read_file, "emptyProcessor.yaml")

    @mark.parametrize(
        "in_file, dup_unit", [("twoUnitsWithSameNameAndCase.yaml", "fullSys"),
            ("twoUnitsWithSameNameAndDifferentCase.yaml", "FULLsYS")])
    def test_two_units_with_same_name_raise_DupElemError(
        self, in_file, dup_unit):
        """Test loading two units with the same name.

        `self` is this test case.
        `in_file` is the processor description file.
        `dup_unit` is the duplicate unit.

        """
        exChk = raises(processor_utils.DupElemError, _read_file, in_file)
        _chk_error(
            [_VerifyPoint(exChk.value.new_element, dup_unit),
             _VerifyPoint(exChk.value.old_element, "fullSys")], exChk.value)


class TestWidth:

    """Test case for checking data path width"""

    @mark.parametrize("in_file", ["twoWideInputOneWideOutputProcessor.yaml",
                                  "busTightOnlyInTheMiddleProcessor.yaml",
                                  "twoInputOneOutputProcessor.yaml"])
    def test_width_less_than_input_capacity_raises_TightWidthError(
        self, in_file):
        """Test a processor with a width less than its input capacity.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        exChk = raises(processor_utils.TightWidthError, _read_file, in_file)
        _chk_error([_VerifyPoint(exChk.value.actual_width, 1),
                    _VerifyPoint(exChk.value.min_width, 2)], exChk.value)

def main():
    """entry point for running test in this module"""
    pytest.main(__file__)


def _chk_error(verify_points, error):
    """Check the specifications of an error.

    `verify_points` are the verification points to assess.
    `error` is the error to assess whose message.
    The function checks the given verification points and that they're
    contained in the error message.

    """
    error = str(error)
    idx = -1

    for cur_point in verify_points:
        cur_point.check(error, idx)


def _chk_two_units(processor):
    """Verify a two-unit processor.

    `processor` is the two-unit processor to assess.
    The function asserts the order and descriptions of units and links
    among them.

    """
    assert processor == ProcessorDesc([UnitModel("input", 1, [])],
        [FuncUnit(UnitModel("output", 1, []), processor.in_ports)], [], [])


def _read_file(file_name):
    """Read a processor description file.

    `file_name` is the processor description file name.
    The function returns the processor description.

    """
    data_dir = "data"
    with open(
        os.path.join(test_env.TEST_DIR, data_dir, file_name)) as proc_file:
        return processor_utils.load_proc_desc(yaml.load(proc_file))


if __name__ == '__main__':
    main()
