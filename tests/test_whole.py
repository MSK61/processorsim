#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""integration tests"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.52.1, python 3.8.7, Fedora release
#               33 (Thirty Three)
#
# notes:        This is a private program.
#
############################################################

from os.path import join

import pytest

from test_utils import TEST_DATA_DIR
import processorSim


class TestWhole:

    """Test case for the whole program functionality"""

    @pytest.mark.parametrize("proc_file_name, prog_file_name, sim_res", [
        ("processorWithALUISA.yaml",
         "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         [["U:full system"]]),
        ("processorWithALUISA.yaml", "2InstructionProgram.asm",
         [["U:full system"], ["", "U:full system"]]),
        ("2WideInput1WideOutputProcessor.yaml", "2InstructionProgram.asm",
         [["U:input", "U:output"], ["U:input", "S:input", "U:output"]]),
        ("2WideALUProcessor.yaml", "RAW.asm",
         [["U:full system"], ["D:full system", "U:full system"]])])
    def test_sim(self, proc_file_name, prog_file_name, sim_res):
        """Test executing a program.

        `self` is this test case.
        `prog_file_name` is the file name of the program to run.
        `sim_res` is the expected simulation result.

        """
        processor_file, program_file = processorSim.get_in_files(
            ["--processor", join(TEST_DATA_DIR, "fullHwDesc", proc_file_name),
             join(TEST_DATA_DIR, "programs", prog_file_name)])
        with processor_file, program_file:
            assert processorSim.get_sim_res(
                processor_file, program_file) == sim_res


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
