#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""integration tests"""

############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
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
# environment:  Komodo IDE, version 11.1.1 build 91033, python 2.7.15,
#               Fedora release 29 (Twenty Nine)
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

    @pytest.mark.parametrize("prog_file_name, sim_res", [
        ("instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
         [["fullSys"]]),
        ("2InstructionProgram.asm", [["fullSys"], ["", "fullSys"]])])
    def test_sim(self, prog_file_name, sim_res):
        """Test executing a program.

        `self` is this test case.
        `prog_file_name` is the file name of the program to run.
        `sim_res` is the expected simulation result.

        """
        processor_file, program_file = processorSim.get_in_files(
            ["--processor",
             join(TEST_DATA_DIR, "fullHwDesc", "processorWithALUISA.yaml"),
             join(TEST_DATA_DIR, "programs", prog_file_name)])
        with processor_file, program_file:
            assert processorSim.get_sim_res(
                processor_file, program_file) == sim_res


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])

if __name__ == '__main__':
    main()