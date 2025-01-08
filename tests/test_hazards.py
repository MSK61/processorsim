#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests pipeline hazards"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025 Mohammed El-Afifi
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
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

import pytest

from test_env import TEST_DIR
from test_type_chks import create_hw_instr
from test_utils import get_lists, get_util_info, get_util_tbl
from processor_utils import ProcessorDesc
from processor_utils.units import FuncUnit, LockInfo, UnitModel
from program_defs import HwInstruction
from sim_services import HwSpec, simulate
from sim_services.sim_defs import StallState


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
            TEST_DIR, 2, {"ALU": False}, LockInfo(True, True)
        )
        assert simulate(
            [create_hw_instr(regs, "ALU") for regs in instr_regs],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], [])),
        ) == get_util_info(
            [[(TEST_DIR, [[0], [1, StallState.DATA]])], [(TEST_DIR, [[1]])]]
        )


class TestInstrOffer:
    """Test case for offering instructions to units"""

    def test_all_candidate_instructions_are_offered_to_the_destinaton_unit(
        self,
    ):
        """Test candidate instructions aren't shortlisted.

        `self` is this test case.

        """
        in_unit = UnitModel(
            "input",
            3,
            {cap: False for cap in ["ALU", "MEM"]},
            LockInfo(True, False),
        )
        out_unit = FuncUnit(
            UnitModel(
                "output", 2, {"ALU": False, "MEM": True}, LockInfo(False, True)
            ),
            [in_unit],
        )
        assert simulate(
            [
                HwInstruction([], *instr_params)
                for instr_params in [
                    ["R1", "MEM"],
                    ["R2", "MEM"],
                    ["R3", "ALU"],
                ]
            ],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], [])),
        ) == get_util_info(
            [
                [("input", get_lists([0, 1, 2]))],
                [
                    ("output", get_lists([0, 2])),
                    ("input", [[1, StallState.STRUCTURAL]]),
                ],
                [("output", [[1]])],
            ]
        )


class TestMemAccess:
    """Test case for instructions with memory access"""

    def test_only_mem_access_instructions_are_checked(self):
        """Test always allowing instructions without memory access.

        `self` is this test case.

        """
        in_unit = UnitModel(
            "input",
            2,
            {cap: False for cap in ["ALU", "MEM"]},
            LockInfo(True, False),
        )
        out_unit = FuncUnit(
            UnitModel(
                "output", 2, {"ALU": False, "MEM": True}, LockInfo(False, True)
            ),
            [in_unit],
        )
        assert simulate(
            [
                HwInstruction([], *instr_params)
                for instr_params in [["R1", "MEM"], ["R2", "ALU"]]
            ],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], [])),
        ) == get_util_tbl([[(unit, [0, 1])] for unit in ["input", "output"]])


class TestRar:
    """Test case for RAR hazards"""

    def test_hazard(self):
        """Test detecting RAR hazards.

        `self` is this test case.

        """
        full_sys_unit = UnitModel(
            TEST_DIR, 2, {"ALU": False}, LockInfo(True, True)
        )
        assert simulate(
            [
                HwInstruction(["R1"], out_reg, "ALU")
                for out_reg in ["R2", "R3"]
            ],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], [])),
        ) == get_util_tbl([[(TEST_DIR, [0, 1])]])


class TestRaw:
    """Test case for RAW hazards"""

    def test_RLock_in_unit_before_WLock(self):  # pylint: disable=invalid-name
        """Test detecting RAW hazards with read locks in earlier units.

        `self` is this test case.

        """
        in_unit, mid, out_unit = (
            UnitModel(name, 1, {"ALU": False}, LockInfo(rd_lock, wr_lock))
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
        assert simulate(
            [
                create_hw_instr(instr_regs, "ALU")
                for instr_regs in [[[], "R1"], [["R1"], "R2"]]
            ],
            HwSpec(proc_desc),
        ) == get_util_info(
            [
                [("input", [[0]])],
                [("input", [[1]]), ("middle", [[0]])],
                [("middle", [[1, StallState.DATA]]), ("output", [[0]])],
                [("middle", [[1]])],
                [("output", [[1]])],
            ]
        )


class TestUnifiedMem:
    """Test case for the unified memory architecture"""

    def test_hazard(self):
        """Test structural hazards in a unified memory architecture.

        `self` is this test case.

        """
        in_unit = UnitModel(
            "input",
            1,
            {cap: True for cap in ["ALU", "MEM"]},
            LockInfo(True, False),
        )
        out_unit = FuncUnit(
            UnitModel(
                "output", 1, {"ALU": False, "MEM": True}, LockInfo(False, True)
            ),
            [in_unit],
        )
        assert simulate(
            [HwInstruction([], out_reg, "ALU") for out_reg in ["R1", "R2"]],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], [])),
        ) == get_util_tbl(
            [
                [("input", [0])],
                [("output", [0]), ("input", [1])],
                [("output", [1])],
            ]
        )


class TestWar:
    """Test case for WAR hazards"""

    def test_write_registers_are_not_checked_in_units_without_write_lock(self):
        """Test opportune write register access check.

        `self` is this test case.

        """
        in_unit = UnitModel("input", 1, {"ALU": False}, LockInfo(False, False))
        out_unit = FuncUnit(
            UnitModel("output", 1, {"ALU": False}, LockInfo(True, True)),
            [in_unit],
        )
        assert simulate(
            [
                create_hw_instr(instr_regs, "ALU")
                for instr_regs in [[["R1"], "R2"], [[], "R1"]]
            ],
            HwSpec(ProcessorDesc([in_unit], [out_unit], [], [])),
        ) == get_util_tbl(
            [
                [("input", [0])],
                [("input", [1]), ("output", [0])],
                [("output", [1])],
            ]
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
