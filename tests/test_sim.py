#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""tests program simulation"""

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
# file:         test_sim.py
#
# function:     simulation tests
#
# description:  tests program simulation on a processor
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.38.0, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################

import pytest
from pytest import mark
import test_utils
from container_utils import BagValDict
import processor
from processor import InstrState, simulate, StallState
import processor_utils
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from str_utils import ICaseString
from test_utils import read_proc_file
from unittest import TestCase


class TestBasic:

    """Test case for basic simulation scenarios"""

    @mark.parametrize("prog, cpu, util_tbl", [
        ([HwInstruction(ICaseString("alu"), ["R11", "R15"], "R14")],
         read_proc_file("processors", "singleALUProcessor.yaml"),
         [{ICaseString("fullSys"): [InstrState(0)]}]),
        ([HwInstruction(*instr_params) for instr_params in [[ICaseString(
            "MEM"), [], "R12"], [ICaseString("ALU"), ["R11", "R15"], "R14"]]],
         read_proc_file(
             "processors", "multiplexedInputSplitOutputProcessor.yaml"),
         [{ICaseString("input"): map(InstrState, [1, 0])},
         {ICaseString("ALU output"): [InstrState(1)],
          ICaseString("MEM output"): [InstrState(0)]}])])
    def test_sim(self, prog, cpu, util_tbl):
        """Test executing a program.

        `self` is this test case.
        `prog` is the program to run.
        `cpu` is the processor to run the program on.
        `util_tbl` is the expected utilization table.

        """
        assert simulate(prog, cpu) == [
            BagValDict(inst_util) for inst_util in util_tbl]


class PipelineTest(TestCase):

    """Test case for instruction flow in the pipeline"""

    def test_instructions_flow_seamlessly(self):
        """Test instructions are moved successfully along the pipeline.

        `self` is this test case.

        """
        big_input = UnitModel(ICaseString("big input"), 4,
                              [ICaseString("ALU")], LockInfo(False, False))
        small_input1 = UnitModel(ICaseString("small input 1"), 1,
                                 [ICaseString("ALU")], LockInfo(False, False))
        mid1 = UnitModel(ICaseString("middle 1"), 1, [ICaseString("ALU")],
                         LockInfo(False, False))
        small_input2 = UnitModel(ICaseString("small input 2"), 1,
                                 [ICaseString("ALU")], LockInfo(False, False))
        mid2 = UnitModel(ICaseString("middle 2"), 2, [ICaseString("ALU")],
                         LockInfo(False, False))
        out_unit = UnitModel(ICaseString("output"), 2, [ICaseString("ALU")],
                             LockInfo(False, False))
        assert simulate([HwInstruction(*instr_params) for instr_params in [
            [ICaseString("ALU"), [], "R1"], [ICaseString("ALU"), [], "R2"],
            [ICaseString("ALU"), [], "R3"], [ICaseString("ALU"), [], "R4"],
            [ICaseString("ALU"), [], "R5"], [ICaseString("ALU"), [], "R6"]]],
            ProcessorDesc([big_input, small_input1, small_input2], [
                FuncUnit(out_unit, [big_input, mid2])], [],
                [FuncUnit(*unit_params) for unit_params in [
                    [mid2, [mid1, small_input2]],
                    [mid1, [small_input1]]]])) == [
                        BagValDict(cp_util) for cp_util in [
                            {ICaseString("big input"):
                             map(InstrState, [0, 1, 2, 3]),
                             ICaseString("small input 1"): [InstrState(4)],
                             ICaseString("small input 2"): [InstrState(5)]},
                            {ICaseString("big input"): map(lambda instr:
                             InstrState(instr, StallState.STRUCTURAL), [2, 3]),
                             ICaseString("output"): map(InstrState, [0, 1]),
                             ICaseString("middle 1"): [InstrState(4)],
                             ICaseString("middle 2"): [InstrState(5)]},
                            {ICaseString("output"): map(InstrState, [2, 3]),
                             ICaseString("middle 2"): map(lambda state_params:
                             InstrState(*state_params),
                             [[5, StallState.STRUCTURAL], [4]])},
                            {ICaseString("output"): map(InstrState, [4, 5])}]]


class TestSim:

    """Test case for program simulation"""

    def test_earlier_instructions_are_propagated_first(self):
        """Test earlier instructions are selected first.

        `self` is this test case.

        """
        inputs = [UnitModel(*unit_params) for unit_params in [
            [ICaseString("ALU input"), 1, [ICaseString("ALU")],
             LockInfo(False, False)], [ICaseString("MEM input"), 1, [
                 ICaseString("MEM")], LockInfo(False, False)]]]
        output = FuncUnit(UnitModel(ICaseString("output"), 1, [ICaseString(
            "ALU"), ICaseString("MEM")], LockInfo(False, False)), inputs)
        TestBasic().test_sim(
            [HwInstruction(*instr_params) for instr_params in [
                [ICaseString("MEM"), [], "R12"],
                [ICaseString("ALU"), ["R11", "R15"], "R14"]]],
            ProcessorDesc(inputs, [output], [], []),
            [{ICaseString("MEM input"): [InstrState(0)],
             ICaseString("ALU input"): [InstrState(1)]},
             {ICaseString("output"): [InstrState(0)],
             ICaseString("ALU input"): [InstrState(1, StallState.STRUCTURAL)]},
             {ICaseString("output"): [InstrState(1)]}])

    @mark.parametrize("prog_file, proc_file, util_info", [
        ("empty.asm", "singleALUProcessor.yaml", []),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "singleALUProcessor.yaml",
         [{ICaseString("fullSys"): [InstrState(0)]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "dualCoreALUProcessor.yaml",
         [{ICaseString("core 1"): [InstrState(0)]}]),
        ("3InstructionProgram.asm", "dualCoreALUProcessor.yaml",
         [{ICaseString("core 1"): [InstrState(0)], ICaseString("core 2"):
           [InstrState(1)]}, {ICaseString("core 1"): [InstrState(2)]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "dualCoreMemALUProcessor.yaml",
         [{ICaseString("core 2"): [InstrState(0)]}]),
        ("2InstructionProgram.asm", "2WideALUProcessor.yaml",
         [{ICaseString("fullSys"): map(InstrState, [0, 1])}]),
        ("3InstructionProgram.asm", "2WideALUProcessor.yaml",
         [{ICaseString("fullSys"): map(InstrState, [0, 1])},
          {ICaseString("fullSys"): [InstrState(2)]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "twoConnectedUnitsProcessor.yaml", [{ICaseString("input"): [
            InstrState(0)]}, {ICaseString("output"): [InstrState(0)]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "3StageProcessor.yaml",
         [{ICaseString("input"): [InstrState(0)]}, {ICaseString("middle"): [
            InstrState(0)]}, {ICaseString("output"): [InstrState(0)]}])])
    def test_processor(self, prog_file, proc_file, util_info):
        """Test simulating a program on the given processor.

        `self` is this test case.
        `prog_file` is the program file.
        `proc_file` is the processor description file.
        `util_info` is the expected utilization information.

        """
        cpu = read_proc_file("processors", proc_file)
        capabilities = processor_utils.get_abilities(cpu)
        TestBasic().test_sim(
            test_utils.compile_prog(prog_file, test_utils.read_isa_file(
                "singleInstructionISA.yaml", capabilities)), cpu, util_info)

    @mark.parametrize("valid_prog", [
        [], [HwInstruction(ICaseString("ALU"), ["R11", "R15"], "R14")]])
    def test_unsupported_instruction_stalls_pipeline(self, valid_prog):
        """Test executing an invalid instruction after a valid program.

        `self` is this test case.
        `valid_prog` is a sequence of valid instructions.

        """
        ex_chk = pytest.raises(processor.StallError, simulate, valid_prog + [
            HwInstruction(ICaseString("MEM"), [], "R14")], read_proc_file(
            "processors", "singleALUProcessor.yaml"))
        test_utils.chk_error([test_utils.ValInStrCheck(
            ex_chk.value.processor_state, len(valid_prog))], ex_chk.value)


class StallTest(TestCase):

    """Test case for stalled instructions"""

    def test_internal_stall_is_detected(self):
        """Test detecting stalls in internal units.

        `self` is this test case.

        """
        in_unit = UnitModel(ICaseString("input"), 2, [ICaseString("ALU")],
                            LockInfo(False, False))
        mid = UnitModel(ICaseString("middle"), 2, [ICaseString("ALU")],
                        LockInfo(False, False))
        out_unit = UnitModel(ICaseString("output"), 1, [ICaseString("ALU")],
                             LockInfo(False, False))
        assert simulate([HwInstruction(*instr_params) for instr_params in [
            [ICaseString("ALU"), [], "R1"], [ICaseString("ALU"), [], "R2"]]],
            ProcessorDesc([in_unit], [FuncUnit(out_unit, [mid])], [],
                          [FuncUnit(mid, [in_unit])])) == [
            BagValDict(cp_util) for cp_util in [
                {ICaseString("input"): map(InstrState, [0, 1])},
                {ICaseString("middle"): map(InstrState, [0, 1])},
                {ICaseString("middle"): [InstrState(1, StallState.STRUCTURAL)],
                 ICaseString("output"): [InstrState(0)]},
                {ICaseString("output"): [InstrState(1)]}]]


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
