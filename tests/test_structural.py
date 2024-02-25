#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests structural hazards"""

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
# file:         test_structural.py
#
# function:     tests for structural hazards
#
# description:  tests structural hazards
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.86.2, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from attr import frozen
import more_itertools
import pytest

from container_utils import BagValDict
import processor_utils
from processor_utils import ProcessorDesc, units
from processor_utils.units import LockInfo, UnitModel2
from program_defs import HwInstruction
from sim_services import HwSpec, simulate
from sim_services.sim_defs import InstrState, StallState
from str_utils import ICaseString


class TestMemUtil:
    """Test case for memory utilization"""

    def test_mem_util_in_earlier_inputs_affects_later_ones(self):
        """Test propagation of memory utilization among inputs.

        `self` is this test case.

        """
        full_sys_unit = UnitModel2(
            ICaseString("full system"),
            2,
            {ICaseString("ALU"): True},
            LockInfo(True, True),
        )
        assert simulate(
            [
                HwInstruction([], out_reg, ICaseString("ALU"))
                for out_reg in ["R1", "R2"]
            ],
            HwSpec(ProcessorDesc([], [], [full_sys_unit], [])),
        ) == [
            BagValDict({ICaseString("full system"): [InstrState(instr)]})
            for instr in [0, 1]
        ]


class TestStructural:
    """Test case for structural hazards"""

    # pylint: disable-next=invalid-name
    def test_mem_ACL_is_correctly_matched_against_instructions(self):
        """Test comparing memory ACL against instructions.

        `self` is this test case.

        """
        assert simulate(
            [
                HwInstruction([], out_reg, ICaseString("ALU"))
                for out_reg in ["R1", "R2"]
            ],
            HwSpec(
                processor_utils.load_proc_desc(
                    {
                        "units": [
                            {
                                units.UNIT_NAME_KEY: "full system",
                                units.UNIT_WIDTH_KEY: 2,
                                units.UNIT_CAPS_KEY: ["ALU"],
                                **{
                                    attr: True
                                    for attr in [
                                        units.UNIT_RLOCK_KEY,
                                        units.UNIT_WLOCK_KEY,
                                    ]
                                },
                                units.UNIT_MEM_KEY: ["ALU"],
                            }
                        ],
                        "dataPath": [],
                    }
                )
            ),
        ) == [
            BagValDict({ICaseString("full system"): [InstrState(instr)]})
            for instr in [0, 1]
        ]


@frozen
class _TestExpResults:
    """Structural test expected results"""

    cp1_util_size: object

    extra_util: object


@frozen
class _TestInParams:
    """Structural test input parameters"""

    width: object

    uses_mem: object

    out_unit_params: object


_STRUCT_CASES = [
    (
        _TestInParams(1, True, [("output", 1, True)]),
        _TestExpResults(
            1,
            [
                {ICaseString("output"): [InstrState(0)]},
                {ICaseString("input"): [InstrState(1)]},
                {ICaseString("output"): [InstrState(1)]},
            ],
        ),
    ),
    (
        _TestInParams(1, False, [("output", 1, True)]),
        _TestExpResults(
            1,
            [
                {
                    ICaseString("output"): [InstrState(0)],
                    ICaseString("input"): [InstrState(1)],
                },
                {ICaseString("output"): [InstrState(1)]},
            ],
        ),
    ),
    (
        _TestInParams(2, False, [("output", 2, True)]),
        _TestExpResults(
            2,
            [
                {
                    ICaseString("output"): [InstrState(0)],
                    ICaseString("input"): [
                        InstrState(1, StallState.STRUCTURAL)
                    ],
                },
                {ICaseString("output"): [InstrState(1)]},
            ],
        ),
    ),
    (
        _TestInParams(
            2,
            False,
            (
                (name, 1, mem_access)
                for name, mem_access in [
                    ("output 1", True),
                    ("output 2", False),
                ]
            ),
        ),
        _TestExpResults(
            2,
            [
                {
                    ICaseString("output 1"): [InstrState(0)],
                    ICaseString("output 2"): [InstrState(1)],
                }
            ],
        ),
    ),
    (
        _TestInParams(
            2, False, ((name, 1, True) for name in ["output 1", "output 2"])
        ),
        _TestExpResults(
            2,
            [
                {
                    ICaseString("output 1"): [InstrState(0)],
                    ICaseString("input"): [
                        InstrState(1, StallState.STRUCTURAL)
                    ],
                },
                {ICaseString("output 1"): [InstrState(1)]},
            ],
        ),
    ),
]


class TestHazards:
    """Test case for structural hazards"""

    @pytest.mark.parametrize("in_params, exp_results", _STRUCT_CASES)
    def test_hazard(self, in_params, exp_results):
        """Test detecting structural hazards.

        `self` is this test case.
        `in_params` are the test input parameters.
        `exp_results` are the test expected results.

        """
        in_unit = UnitModel2(
            ICaseString("input"),
            in_params.width,
            {ICaseString("ALU"): in_params.uses_mem},
            LockInfo(True, False),
        )
        out_units = (
            UnitModel2(
                ICaseString(name),
                width,
                {ICaseString("ALU"): mem_access},
                LockInfo(False, True),
            )
            for name, width, mem_access in in_params.out_unit_params
        )
        out_units = (
            units.FuncUnit(out_unit, [in_unit]) for out_unit in out_units
        )
        cp1_util = {
            ICaseString("input"): map(
                InstrState, range(exp_results.cp1_util_size)
            )
        }
        assert simulate(
            [
                HwInstruction([], out_reg, ICaseString("ALU"))
                for out_reg in ["R1", "R2"]
            ],
            HwSpec(ProcessorDesc([in_unit], out_units, [], [])),
        ) == list(
            map(
                BagValDict,
                more_itertools.prepend(cp1_util, exp_results.extra_util),
            )
        )


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
