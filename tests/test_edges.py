#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests loading edges"""

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
# file:         test_edges.py
#
# function:     edge loading tests
#
# description:  tests loading edges
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.89.1, python 3.11.9, Fedora release
#               40 (Forty)
#
# notes:        This is a private program.
#
############################################################

import itertools
from logging import WARNING

import pytest
from pytest import raises

import test_utils
from test_utils import chk_error, chk_two_units, read_proc_file, ValInStrCheck
import errors
import processor_utils


class TestDupEdge:
    """Test case for loading duplicate edges"""

    def test_two_edges_different_by_case_are_detected(self, caplog):
        """Test loading two edges in different cases.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        chk_two_units(
            "edges", "twoEdgesWithSameUnitNamesAndDifferentCases.yaml"
        )
        assert len(caplog.records) == 3
        unit_warnings = (
            [src_unit, str(["INPUT", "OUTPUT"]), dst_unit]
            for src_unit, dst_unit in [
                ("INPUT", "input"),
                ("OUTPUT", "output"),
            ]
        )
        chk_entries = zip(
            caplog.records,
            itertools.chain(unit_warnings, [str(["input", "output"])]),
        )

        for cur_rec, warn_parts in chk_entries:
            test_utils.chk_warn(warn_parts, cur_rec.getMessage())

    def test_two_identical_edges_are_detected(self, caplog):
        """Test loading two identical edges with the same units.

        `self` is this test case.
        `caplog` is the log capture fixture.

        """
        caplog.set_level(WARNING)
        chk_two_units("edges", "twoEdgesWithSameUnitNamesAndCase.yaml")
        test_utils.chk_warnings([str(["input", "output"])], caplog.records)


class TestEdges:
    """Test case for loading edges"""

    # pylint: disable=invalid-name
    def test_unknown_unit_raises_UndefElemError(self):
        """Test loading an edge involving an unknown unit.

        `self` is this test case.

        """
        ex_chk = raises(
            errors.UndefElemError,
            read_proc_file,
            "edges",
            "edgeWithUnknownUnit.yaml",
        )
        chk_error([ValInStrCheck(ex_chk.value.element, "input")], ex_chk.value)

    @pytest.mark.parametrize(
        "in_file, bad_edge",
        [
            ("emptyEdge.yaml", []),
            ("3UnitEdge.yaml", ["input", "middle", "output"]),
        ],
    )
    def test_wrong_number_of_units_raises_BadEdgeError(
        self, in_file, bad_edge
    ):
        """Test loading an edge with wrong number of units.

        `self` is this test case.
        `in_file` is the processor description file.
        `bad_edge` is the bad edge.

        """
        ex_chk = raises(
            processor_utils.exception.BadEdgeError,
            read_proc_file,
            "edges",
            in_file,
        )
        chk_error([ValInStrCheck(ex_chk.value.edge, bad_edge)], ex_chk.value)


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
