#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests program simulation"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.95.1, python 3.12.7, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

from itertools import chain, starmap

import fastcore.basics
import more_itertools
import pydash
import pytest
from pytest import mark, raises

from test_type_chks import create_hw_instr
import test_utils
from test_utils import get_lists, get_util_info, get_util_tbl, read_proc_file
import processor_utils
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, simulate, StallError
from sim_services.sim_defs import StallState

_SIM_CASES = [
    ("empty.asm", "singleALUProcessor.yaml", []),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "singleALUProcessor.yaml",
        [[("full system", [0])]],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "dualCoreALUProcessor.yaml",
        [[("core 1", [0])]],
    ),
    (
        "3InstructionProgram.asm",
        "dualCoreALUProcessor.yaml",
        [[("core 1", [0]), ("core 2", [1])], [("core 1", [2])]],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "dualCoreMemALUProcessor.yaml",
        [[("core 2", [0])]],
    ),
    (
        "2InstructionProgram.asm",
        "2WideALUProcessor.yaml",
        [[("full system", [0, 1])]],
    ),
    (
        "3InstructionProgram.asm",
        "2WideALUProcessor.yaml",
        [[("full system", [0, 1])], [("full system", [2])]],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "twoConnectedUnitsProcessor.yaml",
        [[("input", [0])], [("output", [0])]],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "3StageProcessor.yaml",
        [[("input", [0])], [("middle", [0])], [("output", [0])]],
    ),
]
_UNITS_DESC = [
    ("big input", 4, True, False),
    ("small input 1", 1, True, False),
    ("middle 1", 1, False, False),
    ("small input 2", 1, True, False),
    ("middle 2", 2, False, False),
    ("output", 2, False, True),
]


class TestBasic:
    """Test case for basic simulation scenarios"""

    @mark.parametrize(
        "prog, cpu, util_tbl",
        [
            (
                [([["R11", "R15"], "R14"], "ALU")],
                read_proc_file("processors", "singleALUProcessor.yaml"),
                [[("full system", [0])]],
            ),
            (
                [([[], "R12"], "MEM"), ([["R11", "R15"], "R14"], "ALU")],
                read_proc_file(
                    "processors", "multiplexedInputSplitOutputProcessor.yaml"
                ),
                [
                    [("input", [1, 0])],
                    [("ALU output", [1]), ("MEM output", [0])],
                ],
            ),
        ],
    )
    def test_sim(self, prog, cpu, util_tbl):
        """Test executing a program.

        `self` is this test case.
        `prog` is the program to run.
        `cpu` is the processor to run the program on.
        `util_tbl` is the expected utilization table.

        """
        assert simulate(
            tuple(starmap(create_hw_instr, prog)), HwSpec(cpu)
        ) == get_util_tbl(util_tbl)


class TestFlow:
    """Test case for instruction flow prioritization"""

    def test_earlier_instructions_are_propagated_first(self):
        """Test earlier instructions are selected first.

        `self` is this test case.

        """
        in_units = [
            UnitModel(name, 1, {categ: False}, LockInfo(True, False))
            for name, categ in [("ALU input", "ALU"), ("MEM input", "MEM")]
        ]
        out_unit = FuncUnit(
            UnitModel(
                "output",
                1,
                {cap: False for cap in ["ALU", "MEM"]},
                LockInfo(False, True),
            ),
            in_units,
        )
        assert simulate(
            fastcore.basics.mapt(
                pydash.spread(HwInstruction),
                [[[], "R12", "MEM"], [["R11", "R15"], "R14", "ALU"]],
            ),
            HwSpec(ProcessorDesc(in_units, [out_unit], [], [])),
        ) == get_util_info(
            [
                [("MEM input", [[0]]), ("ALU input", [[1]])],
                [
                    ("output", [[0]]),
                    ("ALU input", [[1, StallState.STRUCTURAL]]),
                ],
                [("output", [[1]])],
            ]
        )


class TestInSort:
    """Test case for loading instructions into input units"""

    def test_inputs_are_lexicographically_sorted(self):
        """Test instructions are fed into sorted input units.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(name, 1, {"ALU": uses_mem}, LockInfo(rd_lock, wr_lock))
            for name, rd_lock, wr_lock, uses_mem in [
                ("input 1", True, False, False),
                ("output 1", False, True, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit],
            [FuncUnit(out_unit, [in_unit])],
            [UnitModel("input 2", 1, {"ALU": False}, LockInfo(True, False))],
            [],
        )
        assert simulate(
            [HwInstruction([], "R1", "ALU")], HwSpec(proc_desc)
        ) == get_util_tbl([[("input 1", [0])], [("output 1", [0])]])


class TestOutputFlush:
    """Test case for flushing instructions at output ports"""

    @mark.parametrize(
        "extra_instr_lst, last_instr", [([], 2), ([[[], "R3", "ALU"]], 3)]
    )
    def test_stalled_outputs_are_not_flushed(
        self, extra_instr_lst, last_instr
    ):
        """Test data hazards at output ports.

        `self` is this test case.
        `extra_instr_lst` is the extra instructions to execute after the
                          ones causing the hazard.
        `last_instr` is the last instruction number.

        """
        prog = starmap(
            HwInstruction,
            chain([[[], "R1", "ALU"], [["R1"], "R2", "ALU"]], extra_instr_lst),
        )
        cores = starmap(
            lambda name, width: UnitModel(
                name, width, {"ALU": False}, LockInfo(True, True)
            ),
            [("core 1", 1), ("core 2", 1 + len(extra_instr_lst))],
        )
        extra_instr_seq = range(2, last_instr)
        assert simulate(
            tuple(prog), HwSpec(ProcessorDesc([], [], cores, []))
        ) == get_util_info(
            [
                [
                    ("core 1", [[0]]),
                    (
                        "core 2",
                        more_itertools.prepend(
                            [1, StallState.DATA], get_lists(extra_instr_seq)
                        ),
                    ),
                ],
                [("core 2", [[1]])],
            ]
        )


class TestPipeline:
    """Test case for instruction flow in the pipeline"""

    def test_instructions_flow_seamlessly(self):
        """Test instructions are moved successfully along the pipeline.

        `self` is this test case.

        """
        assert simulate(
            [
                HwInstruction([], out_reg, "ALU")
                for out_reg in ["R1", "R2", "R3", "R4", "R5", "R6"]
            ],
            HwSpec(_make_proc_desc(_UNITS_DESC)),
        ) == get_util_info(
            [
                [
                    ("big input", get_lists([0, 1, 2, 3])),
                    ("small input 1", [[4]]),
                    ("small input 2", [[5]]),
                ],
                [
                    (
                        "big input",
                        ([instr, StallState.STRUCTURAL] for instr in [2, 3]),
                    ),
                    ("output", get_lists([0, 1])),
                    ("middle 1", [[4]]),
                    ("middle 2", [[5]]),
                ],
                [
                    ("output", get_lists([2, 3])),
                    ("middle 2", [[5, StallState.STRUCTURAL], [4]]),
                ],
                [("output", get_lists([4, 5]))],
            ]
        )


class TestSim:
    """Test case for program simulation"""

    @mark.parametrize("prog_file, proc_file, util_info", _SIM_CASES)
    def test_processor(self, prog_file, proc_file, util_info):
        """Test simulating a program on the given processor.

        `self` is this test case.
        `prog_file` is the program file.
        `proc_file` is the processor description file.
        `util_info` is the expected utilization information.

        """
        cpu = read_proc_file("processors", proc_file)
        capabilities = processor_utils.get_abilities(cpu)
        assert simulate(
            test_utils.compile_prog(
                prog_file,
                test_utils.read_isa_file(
                    "singleInstructionISA.yaml", capabilities
                ),
            ),
            HwSpec(cpu),
        ) == get_util_tbl(util_info)

    @mark.parametrize(
        "valid_prog, util_tbl",
        [
            ([], []),
            ([(["R11", "R15"], "R14", "ALU")], [[("full system", [0])], {}]),
        ],
    )
    def test_unsupported_instruction_stalls_pipeline(
        self, valid_prog, util_tbl
    ):
        """Test executing an invalid instruction after a valid program.

        `self` is this test case.
        `valid_prog` is a sequence of valid instructions.
        `util_tbl` is the utilization table.

        """
        prog = starmap(HwInstruction, chain(valid_prog, [([], "R14", "MEM")]))
        ex_chk = raises(
            StallError,
            simulate,
            tuple(prog),
            HwSpec(read_proc_file("processors", "singleALUProcessor.yaml")),
        )
        test_utils.chk_error(
            [
                test_utils.ValInStrCheck(
                    ex_chk.value.processor_state, get_util_tbl(util_tbl)
                )
            ],
            ex_chk.value,
        )


class TestStall:
    """Test case for stalled instructions"""

    def test_internal_stall_is_detected(self):
        """Test detecting stalls in internal units.

        `self` is this test case.

        """
        in_unit, mid, out_unit = (
            UnitModel(name, width, {"ALU": False}, LockInfo(rd_lock, wr_lock))
            for name, width, rd_lock, wr_lock in [
                ("input", 2, True, False),
                ("middle", 2, False, False),
                ("output", 1, False, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit],
            [FuncUnit(out_unit, [mid])],
            [],
            [FuncUnit(mid, [in_unit])],
        )
        assert simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in ["R1", "R2"]],
            HwSpec(proc_desc),
        ) == get_util_info(
            [
                [("input", get_lists([0, 1]))],
                [("middle", get_lists([0, 1]))],
                [("middle", [[1, StallState.STRUCTURAL]]), ("output", [[0]])],
                [("output", [[1]])],
            ]
        )


class TestStallErr:
    """Test case for stall error details"""

    def test_util_tbl_exists_in_StallError(  # pylint: disable=invalid-name
        self,
    ):
        """Test dumping the utilizaiton table in stall errors.

        `self` is this test case.

        """
        long_input, mid, short_input, out_unit = (
            UnitModel(name, 1, {"ALU": False}, LockInfo(rd_lock, wr_lock))
            for name, rd_lock, wr_lock in [
                ("long input", False, False),
                ("middle", False, False),
                ("short input", False, False),
                ("output", True, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [long_input, short_input],
            [FuncUnit(out_unit, [mid, short_input])],
            [],
            [FuncUnit(mid, [long_input])],
        )
        cp_util_lst = [
            [("long input", [[0]]), ("short input", [[1]])],
            [("middle", [[0]]), ("output", [[1, StallState.DATA]])],
            [
                ("middle", [[0, StallState.STRUCTURAL]]),
                ("output", [[1, StallState.DATA]]),
            ],
        ]
        assert raises(
            StallError,
            simulate,
            [
                create_hw_instr(instr_regs, "ALU")
                for instr_regs in [[[], "R1"], [["R1"], "R2"]]
            ],
            HwSpec(proc_desc),
        ).value.processor_state == get_util_info(cp_util_lst)


def _make_proc_desc(units_desc):
    """Create a process description.

    `units_desc` is the description of units.

    """
    big_input, small_input1, mid1, small_input2, mid2, out_unit = (
        UnitModel(name, width, {"ALU": False}, LockInfo(rd_lock, wr_lock))
        for name, width, rd_lock, wr_lock in units_desc
    )
    return ProcessorDesc(
        [big_input, small_input1, small_input2],
        [FuncUnit(out_unit, [big_input, mid2])],
        [],
        starmap(
            FuncUnit, [[mid2, [mid1, small_input2]], [mid1, [small_input1]]]
        ),
    )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
