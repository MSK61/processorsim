#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests pipeline hazards"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.74.2, python 3.11.1, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################

import itertools
from unittest import TestCase

import pytest

from test_env import TEST_DIR
from container_utils import BagValDict
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, simulate
from sim_services.sim_defs import InstrState, StallState
from str_utils import ICaseString


class InstrOfferTest(TestCase):

    """Test case for offering instructions to units"""

    def test_all_candidate_instructions_are_offered_to_the_destinaton_unit(
        self,
    ):
        """Test candidate instructions aren't shortlisted.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(
                ICaseString(name),
                width,
                {"ALU": False, "MEM": mem_access},
                LockInfo(rd_lock, wr_lock),
            )
            for name, width, rd_lock, wr_lock, mem_access in [
                ("input", 3, True, False, False),
                ("output", 2, False, True, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], []
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction([], *instr_params)
                    for instr_params in [
                        ["R1", "MEM"],
                        ["R2", "MEM"],
                        ["R3", "ALU"],
                    ]
                ],
                HwSpec(proc_desc),
            ),
            [
                BagValDict(cp_util)
                for cp_util in [
                    {ICaseString("input"): map(InstrState, [0, 1, 2])},
                    {
                        ICaseString("output"): map(InstrState, [0, 2]),
                        ICaseString("input"): [
                            InstrState(1, StallState.STRUCTURAL)
                        ],
                    },
                    {ICaseString("output"): [InstrState(1)]},
                ]
            ],
        )


class MemAccessTest(TestCase):

    """Test case for instructions with memory access"""

    def test_only_mem_access_instructions_are_checked(self):
        """Test always allowing instructions without memory access.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(
                ICaseString(name),
                2,
                {"ALU": False, "MEM": mem_access},
                LockInfo(rd_lock, wr_lock),
            )
            for name, rd_lock, wr_lock, mem_access in [
                ("input", True, False, False),
                ("output", False, True, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], []
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction([], *instr_params)
                    for instr_params in [["R1", "MEM"], ["R2", "ALU"]]
                ],
                HwSpec(proc_desc),
            ),
            [
                BagValDict({ICaseString(unit): map(InstrState, [0, 1])})
                for unit in ["input", "output"]
            ],
        )


class RarTest(TestCase):

    """Test case for RAR hazards"""

    def test_hazard(self):
        """Test detecting RAR hazards.

        `self` is this test case.

        """
        proc_desc = ProcessorDesc(
            [],
            [],
            [
                UnitModel(
                    ICaseString(TEST_DIR),
                    2,
                    {"ALU": False},
                    LockInfo(True, True),
                )
            ],
            [],
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction(["R1"], out_reg, "ALU")
                    for out_reg in ["R2", "R3"]
                ],
                HwSpec(proc_desc),
            ),
            [BagValDict({ICaseString(TEST_DIR): map(InstrState, [0, 1])})],
        )


class RawTest(TestCase):

    """Test case for RAW hazards"""

    # pylint: disable=invalid-name
    def test_RLock_in_unit_before_WLock(self):
        """Test detecting RAW hazards with read locks in earlier units.

        `self` is this test case.

        """
        in_unit, mid, out_unit = (
            UnitModel(
                ICaseString(name),
                1,
                {"ALU": False},
                LockInfo(rd_lock, wr_lock),
            )
            for name, rd_lock, wr_lock in [
                ("input", False, False),
                ("middle", True, False),
                ("output", False, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit],
            [FuncUnit(out_unit, [mid])],
            [],
            [FuncUnit(mid, [in_unit])],
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction(*instr_regs, "ALU")
                    for instr_regs in [[[], "R1"], [["R1"], "R2"]]
                ],
                HwSpec(proc_desc),
            ),
            [
                BagValDict(cp_util)
                for cp_util in [
                    {ICaseString("input"): [InstrState(0)]},
                    {
                        ICaseString("input"): [InstrState(1)],
                        ICaseString("middle"): [InstrState(0)],
                    },
                    {
                        ICaseString("middle"): [
                            InstrState(1, StallState.DATA)
                        ],
                        ICaseString("output"): [InstrState(0)],
                    },
                    {ICaseString("middle"): [InstrState(1)]},
                    {ICaseString("output"): [InstrState(1)]},
                ]
            ],
        )


class TestDataHazards:

    """Test case for data hazards"""

    @pytest.mark.parametrize(
        "instr_regs",
        [
            [[["R1"], "R2"], [[], "R1"]],
            [[[], "R1"], [["R1"], "R2"]],
            [[[], "R1"], [[], "R1"]],
        ],
    )
    def test_hazard(self, instr_regs):
        """Test detecting data hazards.

        `self` is this test case.
        `instr_regs` are the registers accessed by each instruction.

        """
        full_sys_unit = UnitModel(
            ICaseString(TEST_DIR), 2, {"ALU": False}, LockInfo(True, True)
        )
        assert simulate(
            [HwInstruction(*regs, "ALU") for regs in instr_regs],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], [])),
        ) == [
            BagValDict(cp_util)
            for cp_util in [
                {
                    ICaseString(TEST_DIR): itertools.starmap(
                        InstrState, [[0], [1, StallState.DATA]]
                    )
                },
                {ICaseString(TEST_DIR): [InstrState(1)]},
            ]
        ]


class UnifiedMemTest(TestCase):

    """Test case for the unified memory architecture"""

    def test_hazard(self):
        """Test structural hazards in a unified memory architecture.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(
                ICaseString(name),
                1,
                {"ALU": alu_mem_access, "MEM": True},
                LockInfo(rd_lock, wr_lock),
            )
            for name, rd_lock, wr_lock, alu_mem_access in [
                ("input", True, False, True),
                ("output", False, True, False),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], []
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction([], out_reg, "ALU")
                    for out_reg in ["R1", "R2"]
                ],
                HwSpec(proc_desc),
            ),
            [
                BagValDict(cp_util)
                for cp_util in [
                    {ICaseString("input"): [InstrState(0)]},
                    {
                        ICaseString("output"): [InstrState(0)],
                        ICaseString("input"): [InstrState(1)],
                    },
                    {ICaseString("output"): [InstrState(1)]},
                ]
            ],
        )


class WarTest(TestCase):

    """Test case for WAR hazards"""

    def test_write_registers_are_not_checked_in_units_without_write_lock(self):
        """Test opportune write register access check.

        `self` is this test case.

        """
        in_unit, out_unit = (
            UnitModel(
                ICaseString(name),
                1,
                {"ALU": False},
                LockInfo(rd_lock, wr_lock),
            )
            for name, rd_lock, wr_lock in [
                ("input", False, False),
                ("output", True, True),
            ]
        )
        proc_desc = ProcessorDesc(
            [in_unit], [FuncUnit(out_unit, [in_unit])], [], []
        )
        self.assertEqual(
            simulate(
                [
                    HwInstruction(*instr_regs, "ALU")
                    for instr_regs in [[["R1"], "R2"], [[], "R1"]]
                ],
                HwSpec(proc_desc),
            ),
            [
                BagValDict(cp_util)
                for cp_util in [
                    {ICaseString("input"): [InstrState(0)]},
                    {
                        ICaseString("input"): [InstrState(1)],
                        ICaseString("output"): [InstrState(0)],
                    },
                    {ICaseString("output"): [InstrState(1)]},
                ]
            ],
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
