#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor loading service"""

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
# function:     processor loading service tests
#
# description:  tests processor loading
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
from itertools import imap
from mock import patch
import networkx
import pytest
from pytest import mark, raises
from test_utils import chk_error, read_file, ValInStrCheck
import exception
from processor_utils import exceptions, ProcessorDesc
from processor_utils.units import FuncUnit, UnitModel
from unittest import TestCase


class CleanTest(TestCase):

    """Test case for cleaning(optimizing) a processor"""

    def test_data_path_cut_before_output_is_removed(self):
        """Test a data path that ends before reaching an output.

        `self` is this test case.
        Initially a data path never ends before reaching an output(since
        outputs in the first place are taken from where all paths end),
        however due to optimization operations a path may be cut before
        reaching its output so that a dead end may appear.

        """
        with patch("logging.warning") as warn_mock:
            proc_desc = read_file(
                "optimization", "pathThatGetsCutOffItsOutput.yaml")
        assert proc_desc == ProcessorDesc([UnitModel("input", 1, ["ALU"])], [
            FuncUnit(UnitModel("output 1", 1, ["ALU"]), proc_desc.in_ports)],
            [], [])
        _chk_warn(["middle"], warn_mock.call_args)

    def test_incompatible_edge_is_removed(self):
        """Test an edge connecting two incompatible units.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            proc_desc = read_file(
                "optimization", "incompatibleEdgeProcessor.yaml")
        name_input_map = dict(
            imap(lambda in_port: (in_port.name, in_port), proc_desc.in_ports))
        assert proc_desc == ProcessorDesc([UnitModel("input 1", 1, ["ALU"]),
                                           UnitModel("input 2", 1, ["MEM"])], [
            FuncUnit(UnitModel("output 1", 1, ["ALU"]), [name_input_map[
                "input 1"]]), FuncUnit(UnitModel("output 2", 1, ["MEM"]),
                                       [name_input_map["input 2"]])], [], [])
        _chk_warn(["input 2", "output 1"], warn_mock.call_args)

    def test_output_more_capable_than_input(self):
        """Test an output which has more capabilities than the input.

        `self` is this test case.

        """
        in_file = "oneCapabilityInputAndTwoCapabilitiesOutput.yaml"
        proc_desc = read_file("optimization", in_file)
        assert proc_desc == ProcessorDesc(
            [UnitModel("input", 1, ["ALU"])], [FuncUnit(
                UnitModel("output", 1, ["ALU"]), proc_desc.in_ports)], [], [])

    def test_unit_with_empty_capabilities_is_removed(self):
        """Test loading a unit with no capabilities.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            assert read_file("optimization",
                             "unitWithNoCapabilities.yaml") == ProcessorDesc(
                [], [], [UnitModel("core 1", 1, ["ALU"])], [])
        _chk_warn(["core 2"], warn_mock.call_args)


class CoverageTest(TestCase):

    """Test case for fulfilling complete code coverage"""

    def test_FuncUnit_ne_operator(self):
        """Test FuncUnit != operator.

        `self` is this test case.

        """
        assert FuncUnit(UnitModel("", 1, [""]), []) != FuncUnit(
            UnitModel("input", 1, [""]), [])

    def test_ProcessorDesc_ne_operator(self):
        """Test ProcessorDesc != operator.

        `self` is this test case.

        """
        assert ProcessorDesc([], [], [], []) != ProcessorDesc(
            [UnitModel("", 1, [""])], [], [], [])

    def test_ProcessorDesc_repr(self):
        """Test ProcessorDesc representation.

        `self` is this test case.

        """
        in_port = UnitModel("", 1, [""])
        out_port = UnitModel("output", 1, [""])
        repr(ProcessorDesc([in_port], [FuncUnit(out_port, [in_port])], [], []))

    def test_UnitModel_ne_operator(self):
        """Test UnitModel != operator.

        `self` is this test case.

        """
        assert UnitModel("", 1, [""]) != UnitModel("input", 1, [""])


class TestBlocking:

    """Test case for detecting blocked inputs"""

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
        exChk = raises(
            exceptions.DeadInputError, read_file, "blocking", in_file)
        chk_error(
            [ValInStrCheck(exChk.value.port, isolated_input)], exChk.value)


class TestCaps:

    """Test case for loading capabilities"""

    @mark.parametrize(
        "in_file, err_tag", [("processorWithNoCapableInputs.yaml", "input"),
                             ("singleUnitWithNoCapabilities.yaml", "input"),
                             ("emptyProcessor.yaml", "input")])
    def test_processor_with_incapable_ports_raises_EmptyProcError(
            self, in_file, err_tag):
        """Test a processor with no capable ports.

        `self` is this test case.
        `in_file` is the processor description file.
        `err_tag` is the port type tag in the error message.

        """
        assert err_tag in str(raises(exceptions.EmptyProcError, read_file,
                                     "capabilities", in_file).value).lower()

    def test_same_capability_with_different_case_in_two_units_is_detected(
            self):
        """Test loading a capability with different cases in two units.

        `self` is this test case.

        """
        in_file = "twoCapabilitiesWithSameNameAndDifferentCaseInTwoUnits.yaml"
        with patch("logging.warning") as warn_mock:
            assert read_file("capabilities", in_file) == ProcessorDesc(
                [], [], [UnitModel("core 1", 1, ["ALU"]),
                         UnitModel("core 2", 1, ["ALU"])], [])
        _chk_warn(["ALU", "core 1", "alu", "core 2"], warn_mock.call_args)

    @mark.parametrize("in_file, capabilities", [
        ("twoCapabilitiesWithSameNameAndCaseInOneUnit.yaml", ["ALU"]),
        ("twoCapabilitiesWithSameNameAndDifferentCaseInOneUnit.yaml",
         ["ALU", "alu"])])
    def test_two_capabilities_with_same_name_in_one_unit_are_detected(
            self, in_file, capabilities):
        """Test loading two capabilities with the same name in one unit.

        `self` is this test case.
        `in_file` is the processor description file.
        `capabilities` are the identical capabilities.

        """
        with patch("logging.warning") as warn_mock:
            _chk_one_unit("capabilities", in_file)
        _chk_warn(capabilities, warn_mock.call_args)

    @mark.parametrize(
        "in_file, bad_width", [("singleUnitWithZeroWidth.yaml", 0),
                               ("singleUnitWithNegativeWidth.yaml", -1)])
    def test_unit_with_non_positive_width_raises_BadWidthError(
            self, in_file, bad_width):
        """Test loading a unit with a non-positive width.

        `self` is this test case.

        """
        exChk = raises(
            exceptions.BadWidthError, read_file, "capabilities", in_file)
        chk_error([ValInStrCheck(exChk.value.unit, "fullSys"),
                   ValInStrCheck(exChk.value.width, bad_width)], exChk.value)


class TestEdges:

    """Test case for loading edges"""

    def test_edge_with_unknown_unit_raises_UndefElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        exChk = raises(exception.UndefElemError, read_file, "edges",
                       "edgeWithUnknownUnit.yaml")
        chk_error([ValInStrCheck(exChk.value.element, "input")], exChk.value)

    @mark.parametrize("in_file, bad_edge", [("emptyEdge.yaml", []), (
        "3UnitEdge.yaml", ["input", "middle", "output"])])
    def test_edge_with_wrong_number_of_units_raises_BadEdgeError(
            self, in_file, bad_edge):
        """Test loading an edge with wrong number of units.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_edge` is the bad edge.

        """
        exChk = raises(exceptions.BadEdgeError, read_file, "edges", in_file)
        chk_error([ValInStrCheck(exChk.value.edge, bad_edge)], exChk.value)

    def test_three_identical_edges_are_detected(self):
        """Test loading three identical edges with the same units.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            _chk_two_units(
                "edges",
                "3EdgesWithSameUnitNamesAndLowerThenUpperThenMixedCase.yaml")
        assert len(warn_mock.call_args_list) == 2
        chk_entries = itertools.izip(warn_mock.call_args_list, [
            [["input", "output"], ["INPUT", "OUTPUT"]],
            [["input", "output"], ["Input", "Output"]]])

        for cur_call, edge_pair in chk_entries:
            self._chk_edge_warn(edge_pair, cur_call)

    @mark.parametrize(
        "in_file, edges",
        [("twoEdgesWithSameUnitNamesAndCase.yaml", [["input", "output"]]),
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
        with patch("logging.warning") as warn_mock:
            _chk_two_units("edges", in_file)
        self._chk_edge_warn(edges, warn_mock.call_args)

    @staticmethod
    def _chk_edge_warn(edges, warn_call):
        """Verify edges in a warning message.

        `edges` are the edges to assess.
        `warn_call` is the warning function mock call.
        The method asserts that all edges exist in the constructed
        warning message.

        """
        _chk_warn(imap(str, edges), warn_call)


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
        raises(networkx.NetworkXUnfeasible, read_file, "loops", in_file)


class TestProcessors:

    """Test case for loading valid processors"""

    def test_processor_with_one_two_wide_input_and_two_one_wide_outputs(self):
        """Test loading a processor with an input and two outputs.

        `self` is this test case.

        """
        read_file("processors", "oneInputTwoOutputProcessor.yaml")

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = read_file("processors", "4ConnectedUnitsProcessor.yaml")
        assert not proc_desc.in_out_ports
        out_ports = FuncUnit(
            UnitModel("output 1", 1, ["ALU"]), proc_desc.in_ports), FuncUnit(
            UnitModel("output 2", 1, ["ALU"]),
            [proc_desc.internal_units[0].model])
        internal_unit = UnitModel("middle", 1, ["ALU"])
        assert (proc_desc.in_ports, proc_desc.out_ports,
                proc_desc.internal_units) == (
            (UnitModel("input", 1, ["ALU"]),), out_ports,
            (FuncUnit(internal_unit, proc_desc.in_ports),))

    @mark.parametrize(
        "in_file", ["twoConnectedUnitsProcessor.yaml",
                    "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml"])
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        _chk_two_units("processors", in_file)

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        _chk_one_unit("processors", "singleUnitALUProcessor.yaml")


class TestUnits:

    """Test case for loading processor units"""

    @mark.parametrize("in_file, dup_unit", [
        ("twoUnitsWithSameNameAndCase.yaml", "fullSys"),
        ("twoUnitsWithSameNameAndDifferentCase.yaml", "FULLsYS")])
    def test_two_units_with_same_name_raise_DupElemError(
            self, in_file, dup_unit):
        """Test loading two units with the same name.

        `self` is this test case.
        `in_file` is the processor description file.
        `dup_unit` is the duplicate unit.

        """
        exChk = raises(exceptions.DupElemError, read_file, "units", in_file)
        chk_error(
            [ValInStrCheck(exChk.value.new_element, dup_unit),
             ValInStrCheck(exChk.value.old_element, "fullSys")], exChk.value)


class TestWidth:

    """Test case for checking data path width"""

    @mark.parametrize("in_file, capacity, max_width", [
        ("inputPortWithUnconsumedCapability.yaml", 1, 0),
        ("inputPortWithPartiallyConsumedCapability.yaml", 2, 1)])
    def test_not_fully_consumed_capabilitiy_raises_BlockedCapError(
            self, in_file, capacity, max_width):
        """Test an input with a capability not fully consumed.

        `self` is this test case.
        `in_file` is the processor description file.
        `capacity` is the blocked port capacity.
        `max_width` is the processor maximum bus width.

        """
        exChk = raises(
            exceptions.BlockedCapError, read_file, "widths", in_file)
        chk_error([ValInStrCheck("Capability " + exChk.value.capability,
                                 "Capability MEM"), ValInStrCheck(
            "port " + exChk.value.port, "port input"), ValInStrCheck(
            exChk.value.capacity, capacity), ValInStrCheck(
            exChk.value.max_width, max_width)], exChk.value)

    def test_width_less_than_fused_input_capacity_raises_BlockedCapError(self):
        """Test a processor with a width less than its fused capacity.

        `self` is this test case.
        The test runs a scenario where only fused capability flow will
        suffer a tight width problem. Each single capability in this
        scenario can already fully flow with full capacity to the
        output.

        """
        exChk = raises(exceptions.TightWidthError, read_file, "widths",
                       "fusedCapacityLargerThanBusWidth.yaml")
        chk_error([ValInStrCheck(exChk.value.needed_width, 2),
                   ValInStrCheck(exChk.value.actual_width, 1)], exChk.value)


def main():
    """entry point for running test in this module"""
    pytest.main(__file__)


def _chk_one_unit(proc_dir, proc_file):
    """Verify a single unit processor.

    `proc_dir` is the directory containing the processor description file.
    `proc_file` is the processor description file.

    """
    assert read_file(proc_dir, proc_file) == ProcessorDesc(
        [], [], [UnitModel("fullSys", 1, ["ALU"])], [])


def _chk_two_units(proc_dir, proc_file):
    """Verify a two-unit processor.

    `proc_dir` is the directory containing the processor description file.
    `proc_file` is the processor description file.
    The function asserts the order and descriptions of units and links
    among them.

    """
    proc_desc = read_file(proc_dir, proc_file)
    assert proc_desc == ProcessorDesc([UnitModel("input", 1, ["ALU"])], [
        FuncUnit(UnitModel("output", 1, ["ALU"]), proc_desc.in_ports)], [], [])


def _chk_warn(tokens, warn_call):
    """Verify tokens in a warning message.

    `tokens` are the tokens to assess.
    `warn_call` is the warning function mock call.
    The method asserts that all tokens exist in the constructed warning
    message.

    """
    assert warn_call
    warn_msg = warn_call[0][0] % warn_call[0][1:]
    assert all(imap(lambda cap: cap in warn_msg, tokens))


if __name__ == '__main__':
    main()
