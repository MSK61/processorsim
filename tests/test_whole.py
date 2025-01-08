#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""integration tests"""

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
# file:         test_whole.py
#
# function:     integration tests
#
# description:  tests the whole program simulator
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.96.2, python 3.13.1, Fedora release
#               41 (Forty One)
#
# notes:        This is a private program.
#
############################################################

import contextlib
import io
import os.path

import pytest
import typer.testing

import test_utils
import processor_sim


class TestWhole:
    """Test case for the whole program functionality"""

    @pytest.mark.parametrize(
        "proc_file_name, prog_file_name, sim_res",
        [
            (
                "processorWithALUISA.yaml",
                "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma."
                "asm",
                [["U:full system"]],
            ),
            (
                "processorWithALUISA.yaml",
                "2InstructionProgram.asm",
                [["U:full system"], ["", "U:full system"]],
            ),
            (
                "2WideInput1WideOutputProcessor.yaml",
                "2InstructionProgram.asm",
                [["U:input", "U:output"], ["U:input", "S:input", "U:output"]],
            ),
            (
                "2WideALUProcessor.yaml",
                "RAW.asm",
                [["U:full system"], ["D:full system", "U:full system"]],
            ),
        ],
    )
    def test_sim(self, proc_file_name, prog_file_name, sim_res):
        """Test executing a program.

        `self` is this test case.
        `prog_file_name` is the file name of the program to run.
        `sim_res` is the expected simulation result.

        """
        app = typer.Typer()
        app.command()(processor_sim.main)
        file_args = (
            os.path.join(test_utils.TEST_DATA_DIR, *path_parts)
            for path_parts in [
                ["fullHwDesc", proc_file_name],
                ["programs", prog_file_name],
            ]
        )
        with io.StringIO() as exp_res_stream:
            _assert_res(
                typer.testing.CliRunner()
                .invoke(app, ["--processor", *file_args])
                .stdout,
                exp_res_stream,
                sim_res,
            )


def _assert_res(actual_res, exp_res_stream, exp_res):
    """Assert simulation results.

    `actual_res` is the actual simulation results.
    `exp_res_stream` is the expected simulation results stream.
    `exp_res` are the expected simulation results.

    """
    with contextlib.redirect_stdout(exp_res_stream):
        processor_sim.ResultWriter.print_sim_res(exp_res)
    assert actual_res == exp_res_stream.getvalue()


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == "__main__":
    main()
