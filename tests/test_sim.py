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
# file:         test_sim.py
#
# function:     simulation tests
#
# description:  tests program simulation on a processor
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.46.1, python 3.8.3, Fedora release
#               32 (Thirty Two)
#
# notes:        This is a private program.
#
############################################################

import itertools
from itertools import starmap
from unittest import TestCase

import pytest
from pytest import mark, raises

import test_utils
from test_utils import read_proc_file
from container_utils import BagValDict
import processor_utils
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, InstrState, simulate, StallError, StallState
from str_utils import ICaseString


class FlowTest(TestCase):

    """Test case for instruction flow prioritization"""

    def test_earlier_instructions_are_propagated_first(self):
        """Test earlier instructions are selected first.

        `self` is this test case.

        """
        in_units = starmap(lambda name, categ: UnitModel(
            ICaseString(name), 1, [categ], LockInfo(True, False), False),
                           [["ALU input", "ALU"], ["MEM input", "MEM"]])
        in_units = tuple(in_units)
        out_unit = FuncUnit(UnitModel(ICaseString("output"), 1, ["ALU", "MEM"],
                                      LockInfo(False, True), False), in_units)
        assert simulate([HwInstruction(*instr_params) for instr_params in [
            [[], "R12", "MEM"], [["R11", "R15"], "R14", "ALU"]]], HwSpec(
                ProcessorDesc(in_units, [out_unit], [], []))) == [
                    BagValDict(inst_util) for inst_util in
                    [{ICaseString("MEM input"): [InstrState(0)],
                      ICaseString("ALU input"): [InstrState(1)]},
                     {ICaseString("output"): [InstrState(0)], ICaseString(
                         "ALU input"): [InstrState(1, StallState.STRUCTURAL)]},
                     {ICaseString("output"): [InstrState(1)]}]]


class PipelineTest(TestCase):

    """Test case for instruction flow in the pipeline"""

    def test_instructions_are_loaded_to_lexicographically_inputs_first(self):
        """Test instructions are fed into sorted input units.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input 1"), 1, ["ALU"], LockInfo(True, False), False)
        out_unit = FuncUnit(UnitModel(ICaseString("output 1"), 1, ["ALU"],
                                      LockInfo(False, True), True), [in_unit])
        in_out_unit = UnitModel(
            ICaseString("input 2"), 1, ["ALU"], LockInfo(True, False), False)
        assert simulate([HwInstruction([], "R1", "ALU")], HwSpec(ProcessorDesc(
            [in_unit], [out_unit], [in_out_unit], []))) == [BagValDict(
                cp_util) for cp_util in [{ICaseString("input 1"): [InstrState(
                    0)]}, {ICaseString("output 1"): [InstrState(0)]}]]

    def test_instructions_flow_seamlessly(self):
        """Test instructions are moved successfully along the pipeline.

        `self` is this test case.

        """
        big_input = UnitModel(
            ICaseString("big input"), 4, ["ALU"], LockInfo(True, False), False)
        small_input1 = UnitModel(ICaseString("small input 1"), 1, ["ALU"],
                                 LockInfo(True, False), False)
        mid1 = UnitModel(
            ICaseString("middle 1"), 1, ["ALU"], LockInfo(False, False), False)
        small_input2 = UnitModel(ICaseString("small input 2"), 1, ["ALU"],
                                 LockInfo(True, False), False)
        mid2 = UnitModel(
            ICaseString("middle 2"), 2, ["ALU"], LockInfo(False, False), False)
        out_unit = UnitModel(
            ICaseString("output"), 2, ["ALU"], LockInfo(False, True), False)
        proc_desc = ProcessorDesc([big_input, small_input1, small_input2], [
            FuncUnit(out_unit, [big_input, mid2])], [], starmap(FuncUnit, [
                [mid2, [mid1, small_input2]], [mid1, [small_input1]]]))
        assert simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in
             ["R1", "R2", "R3", "R4", "R5", "R6"]],
            HwSpec(proc_desc)) == [BagValDict(cp_util) for cp_util in [
                {ICaseString("big input"): map(InstrState, [0, 1, 2, 3]),
                 ICaseString("small input 1"): [InstrState(4)],
                 ICaseString("small input 2"): [InstrState(5)]},
                {ICaseString("big input"): map(lambda instr: InstrState(
                    instr, StallState.STRUCTURAL), [2, 3]),
                 ICaseString("output"): map(InstrState, [0, 1]),
                 ICaseString("middle 1"): [InstrState(4)],
                 ICaseString("middle 2"): [InstrState(5)]},
                {ICaseString("output"): map(InstrState, [2, 3]),
                 ICaseString("middle 2"):
                 starmap(InstrState, [[5, StallState.STRUCTURAL], [4]])},
                {ICaseString("output"): map(InstrState, [4, 5])}]]


class StallTest(TestCase):

    """Test case for stalled instructions"""

    def test_internal_stall_is_detected(self):
        """Test detecting stalls in internal units.

        `self` is this test case.

        """
        in_unit = UnitModel(
            ICaseString("input"), 2, ["ALU"], LockInfo(True, False), False)
        mid = UnitModel(
            ICaseString("middle"), 2, ["ALU"], LockInfo(False, False), False)
        out_unit = UnitModel(
            ICaseString("output"), 1, ["ALU"], LockInfo(False, True), False)
        proc_desc = ProcessorDesc([in_unit], [FuncUnit(out_unit, [mid])], [],
                                  [FuncUnit(mid, [in_unit])])
        assert simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in ["R1", "R2"]],
            HwSpec(proc_desc)) == [BagValDict(cp_util) for cp_util in [
                {ICaseString("input"): map(InstrState, [0, 1])},
                {ICaseString("middle"): map(InstrState, [0, 1])},
                {ICaseString("middle"): [InstrState(1, StallState.STRUCTURAL)],
                 ICaseString("output"): [InstrState(0)]},
                {ICaseString("output"): [InstrState(1)]}]]

    # pylint: disable=invalid-name
    def test_util_tbl_exists_in_StallError(self):
        """Test dumping the utilizaiton table in stall errors.

        `self` is this test case.

        """
        long_input = UnitModel(ICaseString("long input"), 1, ["ALU"],
                               LockInfo(False, False), False)
        mid = UnitModel(
            ICaseString("middle"), 1, ["ALU"], LockInfo(False, False), False)
        short_input = UnitModel(ICaseString("short input"), 1, ["ALU"],
                                LockInfo(False, False), False)
        out_unit = UnitModel(
            ICaseString("output"), 1, ["ALU"], LockInfo(True, True), False)
        proc_desc = ProcessorDesc([long_input, short_input], [FuncUnit(
            out_unit, [mid, short_input])], [], [FuncUnit(mid, [long_input])])
        assert raises(
            StallError, simulate, [HwInstruction(*instr_regs, "ALU") for
                                   instr_regs in [[[], "R1"], [["R1"], "R2"]]],
            HwSpec(proc_desc)).value.processor_state == [
                BagValDict(cp_util) for cp_util in
                [{ICaseString("long input"): [InstrState(0)],
                  ICaseString("short input"): [InstrState(1)]},
                 {ICaseString("middle"): [InstrState(0)],
                  ICaseString("output"): [InstrState(1, StallState.DATA)]},
                 {ICaseString("middle"):
                  [InstrState(0, StallState.STRUCTURAL)],
                  ICaseString("output"): [InstrState(1, StallState.DATA)]}]]


class TestBasic:

    """Test case for basic simulation scenarios"""

    @mark.parametrize("prog, cpu, util_tbl", [
        ([(["R11", "R15"], "R14", "alu")],
         read_proc_file("processors", "singleALUProcessor.yaml"),
         [{ICaseString("fullSys"): [InstrState(0)]}]),
        ([([], "R12", "MEM"), (["R11", "R15"], "R14", "ALU")], read_proc_file(
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
        assert simulate([HwInstruction(*regs, ICaseString(categ)) for
                         *regs, categ in prog], HwSpec(cpu)) == [
                             BagValDict(inst_util) for inst_util in util_tbl]


class TestOutputFlush:

    """Test case for flushing instructions at output ports"""

    @mark.parametrize("extra_instr_lst", [[], [[[], "R3", "ALU"]]])
    def test_stalled_outputs_are_not_flushed(self, extra_instr_lst):
        """Test data hazards at output ports.

        `self` is this test case.
        `extra_instr_lst` is the extra instructions to execute after the
                          ones causing the hazard.

        """
        program = starmap(HwInstruction, itertools.chain(
            [[[], "R1", "ALU"], [["R1"], "R2", "ALU"]], extra_instr_lst))
        extra_instr_len = len(extra_instr_lst)
        cores = starmap(lambda name, width: UnitModel(
            ICaseString(name), width, ["ALU"], LockInfo(True, True), False),
                        [("core 1", 1), ("core 2", 1 + extra_instr_len)])
        assert simulate(
            tuple(program), HwSpec(ProcessorDesc([], [], cores, []))) == [
                BagValDict(cp_util) for cp_util in
                [{ICaseString("core 1"): [InstrState(0)],
                  ICaseString("core 2"): [InstrState(1, StallState.DATA), *(
                      map(InstrState, range(2, 2 + extra_instr_len)))]},
                 {ICaseString("core 2"): [InstrState(1)]}]]


class TestSim:

    """Test case for program simulation"""

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
        assert simulate(test_utils.compile_prog(
            prog_file, test_utils.read_isa_file(
                "singleInstructionISA.yaml", capabilities)), HwSpec(cpu)) == [
                    BagValDict(inst_util) for inst_util in util_info]

    @mark.parametrize("valid_prog, util_tbl", [
        ([], []), ([(["R11", "R15"], "R14", "ALU")],
                   [{ICaseString("fullSys"): [InstrState(0)]}, {}])])
    def test_unsupported_instruction_stalls_pipeline(
            self, valid_prog, util_tbl):
        """Test executing an invalid instruction after a valid program.

        `self` is this test case.
        `valid_prog` is a sequence of valid instructions.
        `util_tbl` is the utilization table.

        """
        prog = starmap(lambda in_regs, out_reg, categ:
                       HwInstruction(in_regs, out_reg, ICaseString(categ)),
                       valid_prog + [([], "R14", "MEM")])
        ex_chk = raises(StallError, simulate, tuple(prog), HwSpec(
            read_proc_file("processors", "singleALUProcessor.yaml")))
        test_utils.chk_error(
            [test_utils.ValInStrCheck(ex_chk.value.processor_state, [
                BagValDict(cp_util) for cp_util in util_tbl])], ex_chk.value)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
