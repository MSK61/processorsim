#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests program simulation"""

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
# file:         test_sim.py
#
# function:     simulation tests
#
# description:  tests program simulation on a processor
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
#
# notes:        This is a private program.
#
############################################################

import test_utils
import processor
from processor import simulate
import processor_utils
from processor_utils.units import UnitModel
from program_defs import HwInstruction
import pytest
from pytest import mark
from test_utils import read_proc_file


class TestSim:

    """Test case for program simulation"""

    def test_earlier_instructions_are_propagated_first(self):
        """Test earlier instructions are selected first.

        `self` is this test case.

        """
        inputs = [UnitModel("ALU input", 1, ["ALU"]),
                  UnitModel("MEM input", 1, ["MEM"])]
        output = processor_utils.units.FuncUnit(
            UnitModel("output", 1, ["ALU", "MEM"]), inputs)
        self.test_sim([HwInstruction("MEM", [], "R12"), HwInstruction(
            "ALU", ["R11", "R15"], "R14")], processor_utils.ProcessorDesc(
            inputs, [output], [], []), [{"MEM input": [0], "ALU input": [1]}, {
                "output": [0], "ALU input": [1]}, {"output": [1]}])

    @mark.parametrize("prog_file, proc_file, util_info", [
        ("empty.asm", "singleALUProcessor.yaml", []),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "singleALUProcessor.yaml", [{"fullSys": [0]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "dualCoreALUProcessor.yaml", [{"core 1": [0]}]),
        ("3InstructionProgram.asm", "dualCoreALUProcessor.yaml",
         [{"core 1": [0], "core 2": [1]}, {"core 1": [2]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "dualCoreMemALUProcessor.yaml", [{"core 2": [0]}]),
        ("2InstructionProgram.asm", "2WideALUProcessor.yaml",
         [{"fullSys": [0, 1]}]),
        ("3InstructionProgram.asm", "2WideALUProcessor.yaml",
         [{"fullSys": [0, 1]}, {"fullSys": [2]}]),
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         "twoConnectedUnitsProcessor.yaml",
         [{"input": [0]}, {"output": [0]}])])
    def test_processor(self, prog_file, proc_file, util_info):
        """Test simulating a program on the given processor.

        `self` is this test case.
        `prog_file` is the program file.
        `proc_file` is the processor description file.
        `util_info` is the expected utilization information.

        """
        cpu = read_proc_file("processors", proc_file)
        capabilities = processor_utils.get_abilities(cpu)
        self.test_sim(
            test_utils.compile_prog(prog_file, test_utils.read_isa_file(
                "singleInstructionISA.yaml", capabilities)), cpu, util_info)

    @mark.parametrize(
        "prog, cpu, util_tbl",
        [([HwInstruction("alu", ["R11", "R15"], "R14")], read_proc_file(
            "processors", "singleALUProcessor.yaml"), [{"fullSys": [0]}]),
            ([HwInstruction("MEM", [], "R12"),
              HwInstruction("ALU", ["R11", "R15"], "R14")], read_proc_file(
                "processors", "multiplexedInputSplitOutputProcessor.yaml"),
                [{"input": [0, 1]}, {"ALU output": [1], "MEM output": [0]}])])
    def test_sim(self, prog, cpu, util_tbl):
        """Test executing a program.

        `prog` is the program to run.
        `cpu` is the processor to run the program on.
        `util_tbl` is the expected utilization table.

        """
        assert simulate(prog, cpu) == util_tbl

    @mark.parametrize(
        "valid_prog", [[], [HwInstruction("ALU", ["R11", "R15"], "R14")]])
    def test_unsupported_instruction_stalls_pipeline(self, valid_prog):
        """Test executing an invalid instruction after a valid program.

        `self` is this test case.
        `valid_prog` is a sequence of valid instructions.

        """
        ex_chk = pytest.raises(processor.StallError, simulate, valid_prog + [
            HwInstruction("MEM", [], "R14")], read_proc_file(
            "processors", "singleALUProcessor.yaml"))
        test_utils.chk_error([test_utils.ValInStrCheck(
            ex_chk.value.processor_state, len(valid_prog))], ex_chk.value)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])

if __name__ == '__main__':
    main()
