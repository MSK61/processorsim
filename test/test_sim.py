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
from processor_utils import get_abilities
from program_defs import HwInstruction
import pytest
from pytest import mark
from test_utils import compile_prog, read_isa_file, read_proc_file


class TestSim:

    """Test case for program simulation"""

    @mark.parametrize("prog_file, util_info", [
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         [{"core 1": 0}]), ("3InstructionProgram.asm",
                            [{"core 1": 0, "core 2": 1}, {"core 1": 2}])])
    def test_dual_core_processor(self, prog_file, util_info):
        """Test simulating a program on a dual core processor.

        `self` is this test case.
        `prog_file` is the program file.
        `util_info` is the expected utilization information.

        """
        self._test_processor(prog_file, "dualCoreALUProcessor.yaml", util_info)

    @mark.parametrize(
        "prog, cpu, util_tbl",
        [([HwInstruction("alu", ["R11", "R15"], "R14")], read_proc_file(
            "processors", "singleALUUnitProcessor.yaml"), [{"fullSys": 0}])])
    def test_sim(self, prog, cpu, util_tbl):
        """Test executing a program.

        `prog` is the program to run.
        `cpu` is the processor to run the program on.
        `util_tbl` is the expected utilization table.

        """
        assert simulate(prog, cpu) == util_tbl

    @mark.parametrize("prog_file, util_info", [("empty.asm", []), (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        [{"fullSys": 0}])])
    def test_single_unit_processor(self, prog_file, util_info):
        """Test simulating a program on a single-unit processor.

        `self` is this test case.
        `prog_file` is the program file.
        `util_info` is the expected utilization information.

        """
        self._test_processor(
            prog_file, "singleALUUnitProcessor.yaml", util_info)

    def test_unsupported_instruction_raises_InvalidOpError(self):
        """Test executing an invalid instruction.

        `self` is this test case.

        """
        ex_chk = pytest.raises(processor.InvalidOpError, simulate, [
            HwInstruction("MEM", [], "R14")], read_proc_file(
            "processors", "singleALUUnitProcessor.yaml"))
        test_utils.chk_error([test_utils.ValInStrCheck(
            ex_chk.value.operation, "MEM")], ex_chk.value)

    def _test_processor(self, prog_file, proc_file, util_info):
        """Test simulating a program on the given processor.

        `self` is this test case.
        `prog_file` is the program file.
        `proc_file` is the processor description file.
        `util_info` is the expected utilization information.

        """
        cpu = read_proc_file("processors", proc_file)
        capabilities = get_abilities(cpu)
        self.test_sim(compile_prog(prog_file, read_isa_file(
            "singleInstructionISA.yaml", capabilities)), cpu, util_info)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])

if __name__ == '__main__':
    main()
