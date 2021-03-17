#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests program simulation"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.54.3, python 3.8.7, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

import itertools
from unittest import TestCase

import more_itertools
import pytest
from pytest import mark

from test_env import TEST_DIR
from container_utils import BagValDict
import hw_loading
import processor_utils
from processor_utils import ProcessorDesc, units
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, simulate
from sim_services.sim_defs import InstrState, StallState
from str_utils import ICaseString


class RarTest(TestCase):

    """Test case for RAR hazards"""

    def test_hazard(self):
        """Test detecting RAR hazards.

        `self` is this test case.

        """
        proc_desc = ProcessorDesc([], [], [UnitModel(ICaseString(
            TEST_DIR), 2, ["ALU"], LockInfo(True, True), [])], [])
        self.assertEqual(
            simulate([HwInstruction(["R1"], out_reg, "ALU") for out_reg in
                      ["R2", "R3"]], HwSpec(proc_desc)),
            [BagValDict({ICaseString(TEST_DIR): map(InstrState, [0, 1])})])


class RawTest(TestCase):

    """Test case for RAW hazards"""

    # pylint: disable=invalid-name
    def test_RLock_in_unit_before_WLock(self):
        """Test detecting RAW hazards with read locks in earlier units.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input"), 1, ["ALU"], LockInfo(False, False), [])
        mid = UnitModel(
            ICaseString("middle"), 1, ["ALU"], LockInfo(True, False), [])
        out_unit = UnitModel(
            ICaseString("output"), 1, ["ALU"], LockInfo(False, True), [])
        proc_desc = ProcessorDesc([in_unit], [FuncUnit(out_unit, [mid])], [],
                                  [FuncUnit(mid, [in_unit])])
        self.assertEqual(simulate(
            [HwInstruction(*instr_regs, "ALU") for instr_regs in
             [[[], "R1"], [["R1"], "R2"]]],
            HwSpec(proc_desc)), [BagValDict(cp_util) for cp_util in [
                {ICaseString("input"): [InstrState(0)]},
                {ICaseString("input"): [InstrState(1)],
                 ICaseString("middle"): [InstrState(0)]},
                {ICaseString("middle"): [InstrState(1, StallState.DATA)],
                 ICaseString("output"): [InstrState(0)]},
                {ICaseString("middle"): [InstrState(1)]},
                {ICaseString("output"): [InstrState(1)]}]])


class TestDataHazards:

    """Test case for data hazards"""

    @mark.parametrize("instr_regs", [[[["R1"], "R2"], [[], "R1"]], [
        [[], "R1"], [["R1"], "R2"]], [[[], "R1"], [[], "R1"]]])
    def test_hazard(self, instr_regs):
        """Test detecting data hazards.

        `self` is this test case.
        `instr_regs` are the registers accessed by each instruction.

        """
        full_sys_unit = UnitModel(
            ICaseString(TEST_DIR), 2, ["ALU"], LockInfo(True, True), [])
        assert simulate(
            [HwInstruction(*regs, "ALU") for regs in instr_regs],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], []))) == [
                BagValDict(cp_util) for cp_util in
                [{ICaseString(TEST_DIR):
                  itertools.starmap(InstrState, [[0], [1, StallState.DATA]])},
                 {ICaseString(TEST_DIR): [InstrState(1)]}]]


class TestStructural:

    """Test case for structural hazards"""

    @mark.parametrize("in_width, in_mem_util, out_unit_params, extra_util", [
        (1, ["ALU"], [("output", 1, ["ALU"])],
         [{ICaseString("output"): [InstrState(0)]}, {ICaseString("input"): [
             InstrState(1)]}, {ICaseString("output"): [InstrState(1)]}]),
        (1, [], [("output", 1, ["ALU"])],
         [{ICaseString("output"): [InstrState(0)], ICaseString("input"):
           [InstrState(1)]}, {ICaseString("output"): [InstrState(1)]}]),
        (2, [], [("output", 2, ["ALU"])],
         [{ICaseString("output"): [InstrState(0)],
           ICaseString("input"): [InstrState(1, StallState.STRUCTURAL)]},
          {ICaseString("output"): [InstrState(1)]}]),
        (2, [], ((name, 1, mem_access) for name, mem_access in [("output 1", [
            "ALU"]), ("output 2", [])]), [{ICaseString("output 1"): [
                InstrState(0)], ICaseString("output 2"): [InstrState(1)]}]),
        (2, [], ((name, 1, ["ALU"]) for name in ["output 1", "output 2"]),
         [{ICaseString("output 1"): [InstrState(0)],
           ICaseString("input"): [InstrState(1, StallState.STRUCTURAL)]},
          {ICaseString("output 1"): [InstrState(1)]}])])
    def test_hazard(self, in_width, in_mem_util, out_unit_params, extra_util):
        """Test detecting structural hazards.

        `self` is this test case.
        `in_width` is the width of the input unit.
        `in_mem_util` is the list of input unit capabilities requiring
                      memory utilization.
        `out_unit_params` are the creation parameters of output units.
        `extra_util` is the extra utilization beyond the second clock
                     pulse.

        """
        in_unit = UnitModel(ICaseString("input"), in_width, ["ALU"],
                            LockInfo(True, False), in_mem_util)
        out_units = (UnitModel(
            ICaseString(name), width, ["ALU"], LockInfo(False, True),
            mem_access) for name, width, mem_access in out_unit_params)
        out_units = (FuncUnit(out_unit, [in_unit]) for out_unit in out_units)
        cp1_util = {ICaseString("input"): map(InstrState, range(in_width))}
        assert simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in ["R1", "R2"]],
            HwSpec(ProcessorDesc([in_unit], out_units, [], []))) == list(
                map(BagValDict, more_itertools.prepend(cp1_util, extra_util)))

    # pylint: disable=invalid-name
    def test_mem_ACL_is_correctly_matched_against_instructions(self):
        """Test comparing memory ACL against instructions.

        `self` is this test case.

        """
        res_util = (BagValDict({ICaseString("full system"):
                                [InstrState(instr)]}) for instr in [0, 1])
        assert simulate(
            [HwInstruction([], out_reg, ICaseString("ALU")) for out_reg in
             ["R1", "R2"]], HwSpec(processor_utils.load_proc_desc({
                 "units": [hw_loading.make_unit_dict(
                     {units.UNIT_NAME_KEY: "full system",
                      units.UNIT_WIDTH_KEY: 2, units.UNIT_CAPS_KEY:
                      [{"name": "ALU", "memoryAccess": True}],
                      **{attr: True for attr in
                         [units.UNIT_RLOCK_KEY, units.UNIT_WLOCK_KEY]}})],
                 "dataPath": []}))) == list(res_util)
    # pylint: enable=invalid-name

    def test_mem_util_in_earlier_inputs_affects_later_ones(self):
        """Test propagation of memory utilization among inputs.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(ICaseString("full system"), 2, ["ALU"],
                                  LockInfo(True, True), ["ALU"])
        res_util = (BagValDict({ICaseString("full system"):
                                [InstrState(instr)]}) for instr in [0, 1])
        assert simulate([HwInstruction([], out_reg, "ALU") for out_reg in
                         ["R1", "R2"]], HwSpec(ProcessorDesc(
                             [], [], [full_sys_unit], []))) == list(res_util)


class UnifiedMemTest(TestCase):

    """Test case for the unified memory architecture"""

    def test_all_candidate_instructions_are_offered_to_the_destinaton_unit(
            self):
        """Test candidate instructions aren't shortlisted.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input"), 3, ["ALU", "MEM"], LockInfo(True, False), [])
        out_unit = UnitModel(ICaseString("output"), 2, ["ALU", "MEM"],
                             LockInfo(False, True), ["MEM"])
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], [])
        self.assertEqual(simulate([HwInstruction(
            [], *instr_params) for instr_params in [["R1", "MEM"], [
                "R2", "MEM"], ["R3", "ALU"]]], HwSpec(proc_desc)), [BagValDict(
                    cp_util) for cp_util in [{ICaseString("input"): map(
                        InstrState, [0, 1, 2])}, {ICaseString("output"): map(
                            InstrState, [0, 2]), ICaseString("input"): [
                                InstrState(1, StallState.STRUCTURAL)]}, {
                                    ICaseString("output"): [InstrState(1)]}]])

    def test_hazard(self):
        """Test structural hazards in a unified memory architecture.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 1, ["ALU", "MEM"],
                            LockInfo(True, False), ["ALU", "MEM"])
        out_unit = UnitModel(ICaseString("output"), 1, ["ALU", "MEM"],
                             LockInfo(False, True), ["MEM"])
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], [])
        self.assertEqual(simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in ["R1", "R2"]],
            HwSpec(proc_desc)), [BagValDict(cp_util) for cp_util in [
                {ICaseString("input"): [InstrState(0)]},
                {ICaseString("output"): [InstrState(0)], ICaseString("input"):
                 [InstrState(1)]}, {ICaseString("output"): [InstrState(1)]}]])

    def test_only_mem_access_instructions_are_checked(self):
        """Test always allowing instructions without memory access.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input"), 2, ["ALU", "MEM"], LockInfo(True, False), [])
        out_unit = UnitModel(ICaseString("output"), 2, ["ALU", "MEM"],
                             LockInfo(False, True), ["MEM"])
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], [])
        self.assertEqual(
            simulate([HwInstruction([], *instr_params) for instr_params in
                      [["R1", "MEM"], ["R2", "ALU"]]], HwSpec(proc_desc)),
            [BagValDict({ICaseString(unit): map(InstrState, [0, 1])}) for
             unit in ["input", "output"]])


class WarTest(TestCase):

    """Test case for WAR hazards"""

    def test_write_registers_are_not_checked_in_units_without_write_lock(self):
        """Test opportune write register access check.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input"), 1, ["ALU"], LockInfo(False, False), [])
        out_unit = UnitModel(
            ICaseString("output"), 1, ["ALU"], LockInfo(True, True), [])
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], [])
        self.assertEqual(
            simulate([HwInstruction(*instr_regs, "ALU") for instr_regs in
                      [[["R1"], "R2"], [[], "R1"]]], HwSpec(proc_desc)),
            [BagValDict(cp_util) for cp_util in
             [{ICaseString("input"): [InstrState(0)]},
              {ICaseString("input"): [InstrState(1)], ICaseString("output"):
               [InstrState(0)]}, {ICaseString("output"): [InstrState(1)]}]])


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
