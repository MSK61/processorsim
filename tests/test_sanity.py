#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor sanity checks"""

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
# file:         test_sanity.py
#
# function:     tests for processor sanity checks during loading
#
# description:  tests processor sanity checks
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.85.1, python 3.11.7, Fedora release
#               39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################

from attr import frozen
from fastcore.foundation import Self
import networkx
import pytest
from pytest import mark, raises

from test_utils import chk_error, read_proc_file, ValInStrCheck
from processor_utils import exception, load_proc_desc
from processor_utils.exception import PathLockError
from processor_utils.units import (
    UNIT_CAPS_KEY,
    UNIT_NAME_KEY,
    UNIT_RLOCK_KEY,
    UNIT_WIDTH_KEY,
    UNIT_WLOCK_KEY,
)
from str_utils import ICaseString


class TestBlocking:

    """Test case for detecting blocked inputs"""

    @mark.parametrize(
        "in_file, isolated_input",
        [
            ("isolatedInputPort.yaml", "input 2"),
            ("processorWithNoCapableOutputs.yaml", "input"),
        ],
    )
    # pylint: disable-next=invalid-name
    def test_in_port_with_no_compatible_out_links_raises_DeadInputError(
        self, in_file, isolated_input
    ):
        """Test an input port with only incompatible out links.

        `self` is this test case.
        `in_file` is the processor description file.
        `isolated_input` is the input unit that gets isolated during
                         optimization.
        An incompatible link is a link connecting an input port to a
        successor unit with no capabilities in common.

        """
        ex_chk = raises(
            exception.DeadInputError, read_proc_file, "blocking", in_file
        )
        chk_error(
            [ValInStrCheck(ex_chk.value.port, ICaseString(isolated_input))],
            ex_chk.value,
        )


class TestLoop:

    """Test case for loading processors with loops"""

    @mark.parametrize(
        "in_file",
        [
            "selfNodeProcessor.yaml",
            "bidirectionalEdgeProcessor.yaml",
            "bigLoopProcessor.yaml",
        ],
    )
    def test_loop_raises_NetworkXUnfeasible(  # pylint: disable=invalid-name
        self, in_file
    ):
        """Test loading a processor with a loop.

        `self` is this test case.
        `in_file` is the processor description file.

        """
        raises(networkx.NetworkXUnfeasible, read_proc_file, "loops", in_file)


class TestNoLock:

    """Test case for checking paths without locks"""

    @mark.parametrize(
        "units, data_path",
        [
            (
                [
                    {
                        UNIT_NAME_KEY: "input",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        UNIT_WLOCK_KEY: True,
                    },
                    {
                        UNIT_NAME_KEY: "output 1",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                    },
                    {
                        UNIT_NAME_KEY: "output 2",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        UNIT_RLOCK_KEY: True,
                    },
                ],
                [["input", "output 1"], ["input", "output 2"]],
            ),
            (
                [
                    {
                        UNIT_NAME_KEY: "full system",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        UNIT_WLOCK_KEY: True,
                    }
                ],
                [],
            ),
        ],
    )
    # pylint: disable-next=invalid-name
    def test_path_with_no_locks_raises_PathLockError(self, units, data_path):
        """Test loading a processor with no locks in paths.

        `self` is this test case.
        `units` are the processor units.
        `data_path` is the data path between units.

        """
        raises(
            PathLockError,
            load_proc_desc,
            {"units": units, "dataPath": data_path},
        )


class TestPerCap:

    """Test case for checking multiple locks per capability"""

    def test_paths_with_multiple_locks_are_only_detected_per_capability(self):
        """Test detecting multi-lock paths per capability.

        `self` is this test case.
        The method asserts that multiple locks across a path with different
        capabilities don't raise an exception as long as single-capability
        paths don't have multiple locks.

        """
        load_proc_desc(
            {
                "units": [
                    {
                        UNIT_NAME_KEY: "ALU input",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        UNIT_RLOCK_KEY: True,
                    },
                    {
                        UNIT_NAME_KEY: "MEM input",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["MEM"],
                    },
                    {
                        UNIT_NAME_KEY: "center",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU", "MEM"],
                    },
                    {
                        UNIT_NAME_KEY: "ALU output",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["ALU"],
                        UNIT_WLOCK_KEY: True,
                    },
                    {
                        UNIT_NAME_KEY: "MEM output",
                        UNIT_WIDTH_KEY: 1,
                        UNIT_CAPS_KEY: ["MEM"],
                        **{
                            lock_prop: True
                            for lock_prop in [UNIT_RLOCK_KEY, UNIT_WLOCK_KEY]
                        },
                    },
                ],
                "dataPath": [
                    ["ALU input", "center"],
                    ["MEM input", "center"],
                    ["center", "ALU output"],
                    ["center", "MEM output"],
                ],
            }
        )


class TestWidth:

    """Test case for checking data path width"""

    # pylint: disable-next=invalid-name
    def test_unconsumed_capabilitiy_raises_BlockedCapError(self):
        """Test an input with a capability not consumed at all.

        `self` is this test case.

        """
        ex_chk = raises(
            exception.BlockedCapError,
            read_proc_file,
            "widths",
            "inputPortWithUnconsumedCapability.yaml",
        )
        chk_params = [
            ("Capability", Self.capability(), "Capability MEM"),
            ("port", Self.port(), "port input"),
        ]
        chk_error(
            (
                ValInStrCheck(f"{prefix} {val_getter(ex_chk.value)}", exp_val)
                for prefix, val_getter, exp_val in chk_params
            ),
            ex_chk.value,
        )


@frozen
class _IoProcessor:

    """Single input, single output processor"""

    in_unit: object

    out_unit: object

    capability: object


@frozen
class _LockTestData:

    """Lock test data"""

    prop_name: object

    lock_type: object


@frozen
class _TestExpResults:

    """Multi-lock test expected results"""

    in_unit: object

    capability: object


class TestMultiLock:

    """Test case for checking multiple locks along a path"""

    @mark.parametrize(
        "in_proc_desc, lock_data, exp_proc_desc",
        [
            (
                _IoProcessor("input", "output", "ALU"),
                _LockTestData(UNIT_RLOCK_KEY, "read"),
                _TestExpResults("input", "ALU"),
            ),
            (
                _IoProcessor("in_unit", "out_unit", "MEM"),
                _LockTestData(UNIT_WLOCK_KEY, "write"),
                _TestExpResults("in_unit", "MEM"),
            ),
        ],
    )
    # pylint: disable-next=invalid-name
    def test_path_with_multiple_locks_raises_PathLockError(
        self, in_proc_desc, lock_data, exp_proc_desc
    ):
        """Test loading a processor with multiple locks in paths.

        `self` is this test case.
        `in_proc_desc` is the input processor description.
        `lock_data` is the lock test data.
        `exp_proc_desc` is the expected processor description.

        """
        ex_info = raises(
            PathLockError,
            load_proc_desc,
            {
                "units": _get_test_units(in_proc_desc, lock_data.prop_name),
                "dataPath": [[in_proc_desc.in_unit, in_proc_desc.out_unit]],
            },
        )
        assert ex_info.value.start == ICaseString(exp_proc_desc.in_unit)
        assert ex_info.value.lock_type == lock_data.lock_type
        assert ex_info.value.capability == ICaseString(
            exp_proc_desc.capability
        )
        ex_info = str(ex_info.value)

        for part in [
            lock_data.lock_type,
            exp_proc_desc.capability,
            exp_proc_desc.in_unit,
        ]:
            assert part in ex_info


def _get_test_units(proc_desc, lock_prop):
    """Create test units.

    `proc_desc` is the processor description.
    `lock_prop` is the name of the lock property to set.

    """
    return [
        {
            UNIT_NAME_KEY: proc_desc.in_unit,
            UNIT_WIDTH_KEY: 1,
            UNIT_CAPS_KEY: [proc_desc.capability],
            **{lock_prop: True for lock_prop in [UNIT_RLOCK_KEY, lock_prop]},
        },
        {
            UNIT_NAME_KEY: proc_desc.out_unit,
            UNIT_WIDTH_KEY: 1,
            UNIT_CAPS_KEY: [proc_desc.capability],
            **{lock_prop: True for lock_prop in [UNIT_WLOCK_KEY, lock_prop]},
        },
    ]


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
