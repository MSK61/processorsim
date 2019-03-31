#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor loading service"""

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
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 26 (Twenty Six)
#               Komodo IDE, version 11.1.0 build 91033, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
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
from test_utils import chk_error, read_proc_file, ValInStrCheck
import container_utils
import errors
from processor_utils import exception, ProcessorDesc
from processor_utils.units import FuncUnit, UnitModel
import str_utils
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
            proc_desc = read_proc_file(
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
            proc_desc = read_proc_file(
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
        proc_desc = read_proc_file("optimization", in_file)
        assert proc_desc == ProcessorDesc(
            [UnitModel("input", 1, ["ALU"])], [FuncUnit(
                UnitModel("output", 1, ["ALU"]), proc_desc.in_ports)], [], [])

    def test_unit_with_empty_capabilities_is_removed(self):
        """Test loading a unit with no capabilities.

        `self` is this test case.

        """
        with patch("logging.warning") as warn_mock:
            assert read_proc_file(
                "optimization",
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
        ex_chk = raises(
            exception.DeadInputError, read_proc_file, "blocking", in_file)
        chk_error(
            [ValInStrCheck(ex_chk.value.port, isolated_input)], ex_chk.value)


class TestCaps:

    """Test case for loading capabilities"""

    @mark.parametrize("in_file", [
        "processorWithNoCapableInputs.yaml",
        "singleUnitWithNoCapabilities.yaml", "emptyProcessor.yaml"])
    def test_processor_with_incapable_ports_raises_EmptyProcError(
            self, in_file):
        """Test a processor with no capable ports.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        assert "input" in str_utils.ICaseString(
            str(raises(exception.EmptyProcError, read_proc_file,
                       "capabilities", in_file).value))

    def test_same_capability_with_different_case_in_two_units_is_detected(
            self):
        """Test loading a capability with different cases in two units.

        `self` is this test case.

        """
        in_file = "twoCapabilitiesWithSameNameAndDifferentCaseInTwoUnits.yaml"
        with patch("logging.warning") as warn_mock:
            assert read_proc_file("capabilities", in_file) == ProcessorDesc(
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
        `in_file` is the processor description file.
        `bad_width` is the non-positive width.

        """
        ex_chk = raises(
            exception.BadWidthError, read_proc_file, "capabilities", in_file)
        chk_error([ValInStrCheck(ex_chk.value.unit, "fullSys"),
                   ValInStrCheck(ex_chk.value.width, bad_width)], ex_chk.value)


class TestEdges:

    """Test case for loading edges"""

    def test_edge_with_unknown_unit_raises_UndefElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        ex_chk = raises(errors.UndefElemError, read_proc_file, "edges",
                        "edgeWithUnknownUnit.yaml")
        chk_error([ValInStrCheck(ex_chk.value.element, "input")], ex_chk.value)

    @mark.parametrize("in_file, bad_edge", [("emptyEdge.yaml", []), (
        "3UnitEdge.yaml", [u"input", u"middle", u"output"])])
    def test_edge_with_wrong_number_of_units_raises_BadEdgeError(
            self, in_file, bad_edge):
        """Test loading an edge with wrong number of units.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_edge` is the bad edge.

        """
        ex_chk = raises(
            exception.BadEdgeError, read_proc_file, "edges", in_file)
        chk_error([ValInStrCheck(ex_chk.value.edge, bad_edge)], ex_chk.value)

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
            [[u"input", u"output"], [u"INPUT", u"OUTPUT"]],
            [[u"input", u"output"], [u"Input", u"Output"]]])

        for cur_call, edge_pair in chk_entries:
            self._chk_edge_warn(edge_pair, cur_call)

    @mark.parametrize(
        "in_file, edges",
        [("twoEdgesWithSameUnitNamesAndCase.yaml", [[u"input", u"output"]]),
            ("twoEdgesWithSameUnitNamesAndLowerThenUpperCase.yaml",
             [[u"input", u"output"], [u"INPUT", u"OUTPUT"]]),
            ("twoEdgesWithSameUnitNamesAndUpperThenLowerCase.yaml",
             [[u"INPUT", u"OUTPUT"], [u"input", u"output"]])])
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
        raises(networkx.NetworkXUnfeasible, read_proc_file, "loops", in_file)


class TestProcessors:

    """Test case for loading valid processors"""

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = read_proc_file(
            "processors", "4ConnectedUnitsProcessor.yaml")
        assert not proc_desc.in_out_ports
        out_ports = FuncUnit(
            UnitModel("output 1", 1, ["ALU"]), proc_desc.in_ports), FuncUnit(
            UnitModel("output 2", 1, ["ALU"]),
            [proc_desc.internal_units[0].model])
        internal_unit = UnitModel("middle", 1, ["ALU"])
        assert (proc_desc.in_ports, proc_desc.out_ports,
                proc_desc.internal_units) == (
            (UnitModel("input", 1, ["ALU"]),), out_ports,
            [FuncUnit(internal_unit, proc_desc.in_ports)])

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
        _chk_one_unit("processors", "singleALUProcessor.yaml")

    @mark.parametrize(
        "in_file", ["oneInputTwoOutputProcessor.yaml",
                    "inputPortWithPartiallyConsumedCapability.yaml"])
    def test_valid_processor_raises_no_exceptions(self, in_file):
        """Test loading a valid processor raises no exceptions.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        read_proc_file("processors", in_file)


class TestUnits:

    """Test case for loading processor units"""

    def test_processor_retains_unit_post_order(self):
        """Test retaining post-order among units.

        `self` is this test case.

        """
        in_unit = UnitModel("input", 1, ["ALU"])
        in_units = [in_unit]
        mid1 = UnitModel("middle 1", 1, ["ALU"])
        mid1_unit = FuncUnit(mid1, [in_unit])
        mid2 = UnitModel("middle 2", 1, ["ALU"])
        mid2_unit = FuncUnit(mid2, [mid1])
        out_units = [FuncUnit(UnitModel("output", 1, ["ALU"]), [mid2])]
        assert ProcessorDesc(
            in_units, out_units, [], [mid2_unit, mid1_unit]) != ProcessorDesc(
            in_units, out_units, [], [mid1_unit, mid2_unit])

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
        ex_chk = raises(
            exception.DupElemError, read_proc_file, "units", in_file)
        chk_error(
            [ValInStrCheck(ex_chk.value.new_element, dup_unit),
             ValInStrCheck(ex_chk.value.old_element, "fullSys")], ex_chk.value)


class TestWidth:

    """Test case for checking data path width"""

    def test_unconsumed_capabilitiy_raises_BlockedCapError(self):
        """Test an input with a capability not consumed at all.

        `self` is this test case.

        """
        ex_chk = raises(exception.BlockedCapError, read_proc_file, "widths",
                        "inputPortWithUnconsumedCapability.yaml")
        chk_error([ValInStrCheck("Capability " + ex_chk.value.capability,
                                 "Capability MEM"), ValInStrCheck(
            "port " + ex_chk.value.port, "port input")], ex_chk.value)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


def _chk_one_unit(proc_dir, proc_file):
    """Verify a single unit processor.

    `proc_dir` is the directory containing the processor description file.
    `proc_file` is the processor description file.

    """
    assert read_proc_file(proc_dir, proc_file) == ProcessorDesc(
        [], [], [UnitModel("fullSys", 1, ["ALU"])], [])


def _chk_two_units(proc_dir, proc_file):
    """Verify a two-unit processor.

    `proc_dir` is the directory containing the processor description file.
    `proc_file` is the processor description file.
    The function asserts the order and descriptions of units and links
    among them.

    """
    proc_desc = read_proc_file(proc_dir, proc_file)
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
    assert container_utils.contains(warn_call[0][0] % warn_call[0][1:], tokens)


if __name__ == '__main__':
    main()
