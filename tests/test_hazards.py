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
# environment:  Visual Studdio Code 1.44.0, python 3.7.6, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

from unittest import TestCase

import pytest

from test_env import TEST_DIR
from container_utils import BagValDict
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, InstrState, simulate, StallState
from str_utils import ICaseString


class RarTest(TestCase):

    """Test case for RAR hazards"""

    def test_hazard(self):
        """Test detecting RAR hazards.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(ICaseString(TEST_DIR), 2, [
            ICaseString("ALU")], LockInfo(True, True), False)
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[ICaseString("R1")], ICaseString("R2"), ICaseString("ALU")],
              [[ICaseString("R1")], ICaseString("R3"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], []))) == [
                BagValDict(cp_util) for cp_util in [{ICaseString(TEST_DIR): [
                    InstrState(instr) for instr in [0, 1]]}]]


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


class StructuralTest(TestCase):

    """Test case for structural hazards"""

    def test_unified_memory(self):
        """Test detecting hazards with the unified memory architecture.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 1, [ICaseString("ALU")],
                            LockInfo(False, False), True)
        out_unit = FuncUnit(UnitModel(ICaseString("output"), 1, [
            ICaseString("ALU")], LockInfo(False, True), True), [in_unit])
        assert simulate(
            [HwInstruction(*instr_params) for instr_params in
             [[[], ICaseString("R1"), ICaseString("ALU")],
              [[], ICaseString("R2"), ICaseString("ALU")]]],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], []))) == [
                BagValDict(cp_util) for cp_util in [
                    {ICaseString("input"): [InstrState(0)]},
                    {ICaseString("output"): [InstrState(0)]},
                    {ICaseString("input"): [InstrState(1)]},
                    {ICaseString("output"): [InstrState(1)]}]]


class TestDataHazards:

    """Test case for data hazards"""

    @pytest.mark.parametrize("instr_regs", [
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
