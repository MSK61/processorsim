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
# environment:  Visual Studio Code 1.86.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from itertools import chain, starmap

import fastcore.foundation
import more_itertools
import pydash
import pytest
from pytest import mark, raises

from test_type_chks import create_hw_instr
import test_utils
from test_utils import read_proc_file
from container_utils import BagValDict
import processor_utils
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, simulate, StallError
from sim_services.sim_defs import InstrState, StallState
from str_utils import ICaseString

_SIM_CASES = [
    ("empty.asm", "singleALUProcessor.yaml", []),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "singleALUProcessor.yaml",
        [{ICaseString("full system"): [InstrState(0)]}],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "dualCoreALUProcessor.yaml",
        [{ICaseString("core 1"): [InstrState(0)]}],
    ),
    (
        "3InstructionProgram.asm",
        "dualCoreALUProcessor.yaml",
        [
            {
                ICaseString("core 1"): [InstrState(0)],
                ICaseString("core 2"): [InstrState(1)],
            },
            {ICaseString("core 1"): [InstrState(2)]},
        ],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "dualCoreMemALUProcessor.yaml",
        [{ICaseString("core 2"): [InstrState(0)]}],
    ),
    (
        "2InstructionProgram.asm",
        "2WideALUProcessor.yaml",
        [{ICaseString("full system"): map(InstrState, [0, 1])}],
    ),
    (
        "3InstructionProgram.asm",
        "2WideALUProcessor.yaml",
        [
            {ICaseString("full system"): map(InstrState, [0, 1])},
            {ICaseString("full system"): [InstrState(2)]},
        ],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "twoConnectedUnitsProcessor.yaml",
        [
            {ICaseString("input"): [InstrState(0)]},
            {ICaseString("output"): [InstrState(0)]},
        ],
    ),
    (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        "3StageProcessor.yaml",
        [
            {ICaseString("input"): [InstrState(0)]},
            {ICaseString("middle"): [InstrState(0)]},
            {ICaseString("output"): [InstrState(0)]},
        ],
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
                [(["R11", "R15"], "R14", "alu")],
                read_proc_file("processors", "singleALUProcessor.yaml"),
                [{ICaseString("full system"): [InstrState(0)]}],
            ),
            (
                [([], "R12", "MEM"), (["R11", "R15"], "R14", "ALU")],
                read_proc_file(
                    "processors", "multiplexedInputSplitOutputProcessor.yaml"
                ),
                [
                    {ICaseString("input"): map(InstrState, [1, 0])},
                    {
                        ICaseString("ALU output"): [InstrState(1)],
                        ICaseString("MEM output"): [InstrState(0)],
                    },
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
            [
                create_hw_instr(regs, ICaseString(categ))
                for *regs, categ in prog
            ],
            HwSpec(cpu),
        ) == [BagValDict(inst_util) for inst_util in util_tbl]


class TestFlow:
    """Test case for instruction flow prioritization"""

    def test_earlier_instructions_are_propagated_first(self):
        """Test earlier instructions are selected first.

        `self` is this test case.

        """
        in_units = [
            UnitModel(ICaseString(name), 1, [categ], LockInfo(True, False), [])
            for name, categ in [("ALU input", "ALU"), ("MEM input", "MEM")]
        ]
        out_unit = UnitModel(
            ICaseString("output"), 1, ["ALU", "MEM"], LockInfo(False, True), []
        )
        assert simulate(
            fastcore.foundation.mapt(
                pydash.spread(HwInstruction),
                [[[], "R12", "MEM"], [["R11", "R15"], "R14", "ALU"]],
            ),
            HwSpec(
                ProcessorDesc(in_units, [FuncUnit(out_unit, in_units)], [], [])
            ),
        ) == [
            BagValDict(inst_util)
            for inst_util in [
                {
                    ICaseString("MEM input"): [InstrState(0)],
                    ICaseString("ALU input"): [InstrState(1)],
                },
                {
                    ICaseString("output"): [InstrState(0)],
                    ICaseString("ALU input"): [
                        InstrState(1, StallState.STRUCTURAL)
                    ],
                },
                {ICaseString("output"): [InstrState(1)]},
            ]
        ]


class TestInSort:
    """Test case for loading instructions into input units"""

    def test_inputs_are_lexicographically_sorted(self):
        """Test instructions are fed into sorted input units.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(
                ICaseString(name),
                1,
                ["ALU"],
                LockInfo(rd_lock, wr_lock),
                mem_acl,
            )
            for name, rd_lock, wr_lock, mem_acl in [
                ("input 1", True, False, []),
                ("output 1", False, True, ["ALU"]),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit],
            [FuncUnit(out_unit, [in_unit])],
            [
                UnitModel(
                    ICaseString("input 2"),
                    1,
                    ["ALU"],
                    LockInfo(True, False),
                    [],
                )
            ],
            [],
        )
        assert simulate(
            [HwInstruction([], "R1", "ALU")], HwSpec(proc_desc)
        ) == [
            BagValDict(cp_util)
            for cp_util in [
                {ICaseString("input 1"): [InstrState(0)]},
                {ICaseString("output 1"): [InstrState(0)]},
            ]
        ]


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
                ICaseString(name), width, ["ALU"], LockInfo(True, True), []
            ),
            [("core 1", 1), ("core 2", 1 + len(extra_instr_lst))],
        )
        extra_instr_seq = range(2, last_instr)
        assert simulate(
            tuple(prog), HwSpec(ProcessorDesc([], [], cores, []))
        ) == [
            BagValDict(cp_util)
            for cp_util in [
                {
                    ICaseString("core 1"): [InstrState(0)],
                    ICaseString("core 2"): starmap(
                        InstrState,
                        more_itertools.prepend(
                            [1, StallState.DATA],
                            ([instr] for instr in extra_instr_seq),
                        ),
                    ),
                },
                {ICaseString("core 2"): [InstrState(1)]},
            ]
        ]


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
        ) == [
            BagValDict(cp_util)
            for cp_util in [
                {
                    ICaseString("big input"): map(InstrState, [0, 1, 2, 3]),
                    ICaseString("small input 1"): [InstrState(4)],
                    ICaseString("small input 2"): [InstrState(5)],
                },
                {
                    ICaseString("big input"): (
                        InstrState(instr, StallState.STRUCTURAL)
                        for instr in [2, 3]
                    ),
                    ICaseString("output"): map(InstrState, [0, 1]),
                    ICaseString("middle 1"): [InstrState(4)],
                    ICaseString("middle 2"): [InstrState(5)],
                },
                {
                    ICaseString("output"): map(InstrState, [2, 3]),
                    ICaseString("middle 2"): starmap(
                        InstrState, [[5, StallState.STRUCTURAL], [4]]
                    ),
                },
                {ICaseString("output"): map(InstrState, [4, 5])},
            ]
        ]


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
        ) == [BagValDict(inst_util) for inst_util in util_info]

    @mark.parametrize(
        "valid_prog, util_tbl",
        [
            ([], []),
            (
                [(["R11", "R15"], "R14", "ALU")],
                [{ICaseString("full system"): [InstrState(0)]}, {}],
            ),
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
        prog = starmap(
            lambda in_regs, out_reg, categ: HwInstruction(
                in_regs, out_reg, ICaseString(categ)
            ),
            chain(valid_prog, [([], "R14", "MEM")]),
        )
        ex_chk = raises(
            StallError,
            simulate,
            tuple(prog),
            HwSpec(read_proc_file("processors", "singleALUProcessor.yaml")),
        )
        test_utils.chk_error(
            [
                test_utils.ValInStrCheck(
                    ex_chk.value.processor_state,
                    [BagValDict(cp_util) for cp_util in util_tbl],
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
            UnitModel(
                ICaseString(name),
                width,
                ["ALU"],
                LockInfo(rd_lock, wr_lock),
                [],
            )
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
        ) == [
            BagValDict(cp_util)
            for cp_util in [
                {ICaseString("input"): map(InstrState, [0, 1])},
                {ICaseString("middle"): map(InstrState, [0, 1])},
                {
                    ICaseString("middle"): [
                        InstrState(1, StallState.STRUCTURAL)
                    ],
                    ICaseString("output"): [InstrState(0)],
                },
                {ICaseString("output"): [InstrState(1)]},
            ]
        ]


class TestStallErr:
    """Test case for stall error details"""

    def test_util_tbl_exists_in_StallError(  # pylint: disable=invalid-name
        self,
    ):
        """Test dumping the utilizaiton table in stall errors.

        `self` is this test case.

        """
        long_input, mid, short_input, out_unit = (
            UnitModel(
                ICaseString(name), 1, ["ALU"], LockInfo(rd_lock, wr_lock), []
            )
            for name, rd_lock, wr_lock in [
                ("long input", False, False),
                ("middle", False, False),
                ("short input", False, False),
                ("output", True, True),
            ]
        )
        cp_util_lst = [
            {
                ICaseString("long input"): [InstrState(0)],
                ICaseString("short input"): [InstrState(1)],
            },
            {
                ICaseString("middle"): [InstrState(0)],
                ICaseString("output"): [InstrState(1, StallState.DATA)],
            },
            {
                ICaseString("middle"): [InstrState(0, StallState.STRUCTURAL)],
                ICaseString("output"): [InstrState(1, StallState.DATA)],
            },
        ]
        assert raises(
            StallError,
            simulate,
            [
                create_hw_instr(instr_regs, "ALU")
                for instr_regs in [[[], "R1"], [["R1"], "R2"]]
            ],
            HwSpec(
                ProcessorDesc(
                    [long_input, short_input],
                    [FuncUnit(out_unit, [mid, short_input])],
                    [],
                    [FuncUnit(mid, [long_input])],
                )
            ),
        ).value.processor_state == list(map(BagValDict, cp_util_lst))


def _make_proc_desc(units_desc):
    """Create a process description.

    `units_desc` is the description of units.

    """
    big_input, small_input1, mid1, small_input2, mid2, out_unit = (
        UnitModel(
            ICaseString(name), width, ["ALU"], LockInfo(rd_lock, wr_lock), []
        )
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
