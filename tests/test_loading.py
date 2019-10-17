#!/usr/bin/env python3
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
# file:         test_loading.py
#
# function:     processor loading service tests
#
# description:  tests processor loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.39.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

from logging import WARNING

import pytest
from pytest import mark, raises

from test_utils import chk_error, chk_two_units, chk_warn, read_proc_file, \
    ValInStrCheck
import container_utils
import errors
import processor_utils
from processor_utils import exception, ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from str_utils import ICaseString


class TestCaps:

    """Test case for loading capabilities"""

    # pylint: disable=invalid-name
    @mark.parametrize("in_file", [
        "processorWithNoCapableInputs.yaml",
        "singleUnitWithNoCapabilities.yaml", "emptyProcessor.yaml"])
    def test_processor_with_incapable_ports_raises_EmptyProcError(
            self, in_file):
        """Test a processor with no capable ports.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        assert "input" in ICaseString(
            str(raises(exception.EmptyProcError, read_proc_file,
                       "capabilities", in_file).value))
    # pylint: enable=invalid-name

    def test_same_capability_with_different_case_in_two_units_is_detected(
            self, caplog):
        """Test loading a capability with different cases in two units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        in_file = "twoCapabilitiesWithSameNameAndDifferentCaseInTwoUnits.yaml"
        assert read_proc_file("capabilities", in_file) == ProcessorDesc(
            [], [], map(lambda unit_params: UnitModel(*unit_params), [
                [ICaseString("core 1"), 1, [ICaseString("ALU")],
                 LockInfo(False, False)], [ICaseString("core 2"), 1, [
                     ICaseString("ALU")], LockInfo(False, False)]]), [])
        chk_warn(["ALU", "core 1", "alu", "core 2"], caplog.records)
        assert ICaseString.__name__ not in caplog.records[0].getMessage()

    @mark.parametrize("in_file, capabilities", [
        ("twoCapabilitiesWithSameNameAndCaseInOneUnit.yaml", ["ALU"]),
        ("twoCapabilitiesWithSameNameAndDifferentCaseInOneUnit.yaml",
         ["ALU", "alu"])])
    def test_two_capabilities_with_same_name_in_one_unit_are_detected(
            self, caplog, in_file, capabilities):
        """Test loading two capabilities with the same name in one unit.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `in_file` is the processor description file.
        `capabilities` are the identical capabilities.

        """
        caplog.set_level(WARNING)
        _chk_one_unit("capabilities", in_file)
        chk_warn(capabilities, caplog.records)

    # pylint: disable=invalid-name
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
    # pylint: enable=invalid-name


class TestEdges:

    """Test case for loading edges"""

    # pylint: disable=invalid-name
    def test_edge_with_unknown_unit_raises_UndefElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        ex_chk = raises(errors.UndefElemError, read_proc_file, "edges",
                        "edgeWithUnknownUnit.yaml")
        chk_error([ValInStrCheck(ex_chk.value.element, ICaseString("input"))],
                  ex_chk.value)

    @mark.parametrize("in_file, bad_edge", [("emptyEdge.yaml", []), (
        "3UnitEdge.yaml", ["input", "middle", "output"])])
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
    # pylint: enable=invalid-name

    def test_three_identical_edges_are_detected(self, caplog):
        """Test loading three identical edges with the same units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        chk_two_units(
            "edges",
            "3EdgesWithSameUnitNamesAndLowerThenUpperThenMixedCase.yaml")
        assert len(caplog.records) == 2
        chk_entries = zip(
            caplog.records, [[["input", "output"], ["INPUT", "OUTPUT"]],
                             [["input", "output"], ["Input", "Output"]]])

        for cur_rec, edge_pair in chk_entries:
            self._chk_edge_warn(edge_pair, cur_rec)

    @mark.parametrize(
        "in_file, edges",
        [("twoEdgesWithSameUnitNamesAndCase.yaml", [["input", "output"]]),
         ("twoEdgesWithSameUnitNamesAndLowerThenUpperCase.yaml",
          [["input", "output"], ["INPUT", "OUTPUT"]]),
         ("twoEdgesWithSameUnitNamesAndUpperThenLowerCase.yaml",
          [["INPUT", "OUTPUT"], ["input", "output"]])])
    def test_two_identical_edges_are_detected(self, caplog, in_file, edges):
        """Test loading two identical edges with the same units.

        `self` is this test case.
        `caplog` is the log capture fixture.
        `in_file` is the processor description file.
        `edges` are the identical edges.

        """
        caplog.set_level(WARNING)
        chk_two_units("edges", in_file)
        assert caplog.records
        self._chk_edge_warn(edges, caplog.records[0])

    @staticmethod
    def _chk_edge_warn(edges, warn_call):
        """Verify edges in a warning message.

        `edges` are the edges to assess.
        `warn_call` is the warning function mock call.
        The method asserts that all edges exist in the constructed
        warning message.

        """
        assert container_utils.contains(
            warn_call.getMessage(), map(str, edges))


class TestProcessors:

    """Test case for loading valid processors"""

    def test_processor_with_explicit_unit_locks(self):
        """Test loading a processor with explicitly defined unit locks.

        `self` is this test case.

        """
        assert processor_utils.load_proc_desc(
            {"units": [{"name": "fullSys", "width": 1, "capabilities": ["ALU"],
                        "readLock": True, "writeLock": True}],
             "dataPath": []}) == ProcessorDesc(
                 [], [], [UnitModel(ICaseString("fullSys"), 1, [
                     ICaseString("ALU")], LockInfo(True, True))], [])

    def test_processor_with_four_connected_functional_units(self):
        """Test loading a processor with four functional units.

        `self` is this test case.

        """
        proc_desc = read_proc_file(
            "processors", "4ConnectedUnitsProcessor.yaml")
        assert not proc_desc.in_out_ports
        alu_cap = ICaseString("ALU")
        lock_info = LockInfo(False, False)
        out_ports = tuple(FuncUnit(*unit_params) for unit_params in [
            [UnitModel(ICaseString("output 1"), 1, [alu_cap], lock_info),
             proc_desc.in_ports],
            [UnitModel(ICaseString("output 2"), 1, [alu_cap], lock_info),
             map(lambda unit: unit.model, proc_desc.internal_units)]])
        in_unit = ICaseString("input")
        internal_unit = UnitModel(
            ICaseString("middle"), 1, [alu_cap], lock_info)
        assert (proc_desc.in_ports, proc_desc.out_ports,
                proc_desc.internal_units) == (
                    (UnitModel(in_unit, 1, [alu_cap], lock_info),), out_ports,
                    (FuncUnit(internal_unit, proc_desc.in_ports),))

    @mark.parametrize(
        "in_file", ["twoConnectedUnitsProcessor.yaml",
                    "edgeWithUnitNamesInCaseDifferentFromDefinition.yaml"])
    def test_processor_with_two_connected_functional_units(self, in_file):
        """Test loading a processor with two functional units.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        chk_two_units("processors", in_file)

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
        in_unit = UnitModel(ICaseString("input"), 1, [ICaseString("ALU")],
                            LockInfo(False, False))
        in_units = [in_unit]
        mid1 = UnitModel(ICaseString("middle 1"), 1, [ICaseString("ALU")],
                         LockInfo(False, False))
        mid1_unit = FuncUnit(mid1, [in_unit])
        mid2 = UnitModel(ICaseString("middle 2"), 1, [ICaseString("ALU")],
                         LockInfo(False, False))
        mid2_unit = FuncUnit(mid2, [mid1])
        out_units = [FuncUnit(UnitModel(ICaseString("output"), 1, [
            ICaseString("ALU")], LockInfo(False, False)), [mid2])]
        assert ProcessorDesc(
            in_units, out_units, [], [mid2_unit, mid1_unit]) != ProcessorDesc(
                in_units, out_units, [], [mid1_unit, mid2_unit])

    # pylint: disable=invalid-name
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
            [ValInStrCheck(ex_chk.value.new_element, ICaseString(dup_unit)),
             ValInStrCheck(ex_chk.value.old_element, ICaseString("fullSys"))],
            ex_chk.value)
    # pylint: enable=invalid-name


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


def _chk_one_unit(proc_dir, proc_file):
    """Verify a single unit processor.

    `proc_dir` is the directory containing the processor description file.
    `proc_file` is the processor description file.

    """
    assert read_proc_file(proc_dir, proc_file) == ProcessorDesc([], [], [
        UnitModel(ICaseString("fullSys"), 1, [ICaseString("ALU")],
                  LockInfo(False, False))], [])


if __name__ == '__main__':
    main()