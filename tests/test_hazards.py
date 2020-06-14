#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests program simulation"""

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
# file:         test_hazards.py
#
# function:     hazard tests
#
# description:  tests hazards during program simulation
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.46.0, python 3.8.3, Fedora release
#               32 (Thirty Two)
#
# notes:        This is a private program.
#
############################################################

import itertools
from unittest import TestCase

from more_itertools import prepend
import pytest
from pytest import mark

from test_env import TEST_DIR
from container_utils import BagValDict
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, InstrState, simulate, StallState
from str_utils import ICaseString


class MemUtilTest(TestCase):

    """Test case for memory utilization propagation across units"""

    def test_mem_busy_doesnt_affect_units_without_mem_util(self):
        """Test no effect on units without memory access.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 2, [ICaseString("ALU")],
                            LockInfo(True, False), False)
        out_units = [
            FuncUnit(UnitModel(ICaseString("output 1"), 1, [
                ICaseString("ALU")], LockInfo(False, True), True), [in_unit]),
            FuncUnit(UnitModel(ICaseString("output 2"), 1, [
                ICaseString("ALU")], LockInfo(False, True), False), [in_unit])]
        instructions = map(InstrState, range(2))
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([in_unit], out_units, [], []))) == list(
                map(BagValDict, [{ICaseString("input"): list(instructions)},
                                 {ICaseString("output 1"): [InstrState(0)],
                                  ICaseString("output 2"): [InstrState(1)]}]))


class RarTest(TestCase):

    """Test case for RAR hazards"""

    def test_hazard(self):
        """Test detecting RAR hazards.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(ICaseString(TEST_DIR), 2, [
            ICaseString("ALU")], LockInfo(True, True), False)
        instructions = map(InstrState, range(2))
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[ICaseString("R1")], ICaseString("R2"), ICaseString("ALU")],
              [[ICaseString("R1")], ICaseString("R3"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], []))) == list(
                map(BagValDict, [{ICaseString(TEST_DIR): list(instructions)}]))


class RawTest(TestCase):

    """Test case for RAW hazards"""

    # pylint: disable=invalid-name
    def test_RLock_in_unit_before_WLock(self):
        """Test detecting RAW hazards with read locks in earlier units.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 1, [ICaseString("ALU")],
                            LockInfo(False, False), False)
        mid = UnitModel(ICaseString("middle"), 1, [ICaseString("ALU")],
                        LockInfo(True, False), False)
        out_unit = UnitModel(ICaseString("output"), 1, [ICaseString("ALU")],
                             LockInfo(False, True), False)
        proc_desc = ProcessorDesc([in_unit], [FuncUnit(out_unit, [mid])], [],
                                  [FuncUnit(mid, [in_unit])])
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[ICaseString("R1")], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(proc_desc)) == [BagValDict(cp_util) for cp_util in [
                {ICaseString("input"): [InstrState(0)]},
                {ICaseString("input"): [InstrState(1)],
                 ICaseString("middle"): [InstrState(0)]},
                {ICaseString("middle"): [InstrState(1, StallState.DATA)],
                 ICaseString("output"): [InstrState(0)]},
                {ICaseString("middle"): [InstrState(1)]},
                {ICaseString("output"): [InstrState(1)]}]]


class TestDataHazards:

    """Test case for data hazards"""

    @mark.parametrize("instr_regs", [
        [[[ICaseString("R1")], ICaseString("R2")], [[], ICaseString("R1")]],
        [[[], ICaseString("R1")], [[ICaseString("R1")], ICaseString("R2")]],
        [[[], ICaseString("R1")], [[], ICaseString("R1")]]])
    def test_hazard(self, instr_regs):
        """Test detecting data hazards.

        `self` is this test case.
        `instr_regs` are the registers accessed by each instruction.

        """
        full_sys_unit = UnitModel(ICaseString(TEST_DIR), 2, [
            ICaseString("ALU")], LockInfo(True, True), False)
        assert simulate(
            [HwInstruction(*reg_lst, ICaseString("ALU")) for reg_lst in
             instr_regs],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], []))) == [
                BagValDict(cp_util) for cp_util in [{ICaseString(TEST_DIR): [
                    InstrState(0), InstrState(1, StallState.DATA)]}, {
                        ICaseString(TEST_DIR): [InstrState(1)]}]]


class TestStructural:

    """Test case for structural hazards"""

    @mark.parametrize(
        "in_mem_util, mid_cp_util",
        [(True, [{ICaseString("output"): [InstrState(0)]}, {ICaseString(
            "input"): [InstrState(1)]}]), (False, [{ICaseString("output"): [
                InstrState(0)], ICaseString("input"): [InstrState(1)]}])])
    def test_hazard(self, in_mem_util, mid_cp_util):
        """Test detecting structural hazards.

        `self` is this test case.
        `in_mem_util` is the input unit memory utilization flag.
        `mid_cp_util` is unit utilization for middle clock pulses.

        """
        in_unit = UnitModel(ICaseString("input"), 1, [ICaseString("ALU")],
                            LockInfo(True, False), in_mem_util)
        out_unit = FuncUnit(UnitModel(ICaseString("output"), 1, [
            ICaseString("ALU")], LockInfo(False, True), True), [in_unit])
        res_util = itertools.chain(prepend({ICaseString("input"): [InstrState(
            0)]}, mid_cp_util), [{ICaseString("output"): [InstrState(1)]}])
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], []))) == [
                BagValDict(cp_util) for cp_util in res_util]

    def test_mem_util_in_earlier_inputs_affects_later_ones(self):
        """Test propagation of memory utilization among inputs.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(ICaseString("fullSys"), 2, [
            ICaseString("ALU")], LockInfo(True, False), True)
        res_util = map(lambda instr: BagValDict(
            {ICaseString("fullSys"): [InstrState(instr)]}), range(2))
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], []))) == list(
                res_util)

    @mark.parametrize("main_out_unit, extra_out_units, out_width",
                      [("output", [], 2), ("output 1", ["output 2"], 1)])
    def test_mem_util_is_allowed_once_in_destination_units(
            self, main_out_unit, extra_out_units, out_width):
        """Test propagation of memory utilization among consumer units.

        `self` is this test case.
        `main_out_unit` is the main output unit name.
        `extra_out_units` are the names of extra output units.
        `out_width` is the width of output units.

        """
        in_unit = UnitModel(ICaseString("input"), 2, [ICaseString("ALU")],
                            LockInfo(True, False), False)
        out_units = map(lambda output: UnitModel(
            ICaseString(output), out_width, [ICaseString("ALU")], LockInfo(
                False, True), True), prepend(main_out_unit, extra_out_units))
        out_units = map(lambda output: FuncUnit(output, [in_unit]), out_units)
        instructions = map(InstrState, range(2))
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([in_unit], out_units, [], []))) == list(
                map(BagValDict, [{ICaseString("input"): list(instructions)}, {
                    ICaseString("input"):
                    [InstrState(1, StallState.STRUCTURAL)],
                    ICaseString(main_out_unit): [InstrState(0)]}, {
                        ICaseString(main_out_unit): [InstrState(1)]}]))


class WarTest(TestCase):

    """Test case for WAR hazards"""

    def test_write_registers_are_not_checked_in_units_without_write_lock(self):
        """Test opportune write register access check.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 1, [ICaseString("ALU")],
                            LockInfo(False, False), False)
        out_unit = FuncUnit(UnitModel(ICaseString("output"), 1, [
            ICaseString("ALU")], LockInfo(True, True), False), [in_unit])
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[ICaseString("R1")], ICaseString("R2"), ICaseString("ALU")], [
                 [], ICaseString("R1"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], []))) == [
                BagValDict(cp_util) for cp_util in
                [{ICaseString("input"): [InstrState(0)]},
                 {ICaseString("input"): [InstrState(1)], ICaseString("output"):
                  [InstrState(0)]}, {ICaseString("output"): [InstrState(1)]}]]


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
