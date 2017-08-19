#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests program simulation"""

############################################################
#
# Copyright 2017 Mohammed El-Afifi
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
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#
# notes:        This is a private program.
#
############################################################

import test_utils
import processor
import processor_utils
import pytest


class TestSim:

    """Test case for program simulation"""

    @pytest.mark.parametrize("prog_file, util_info", [("empty.asm", []), (
        "instructionWithOneSpaceBeforeOperandsAndNoSpacesAroundComma.asm",
        [{"fullSys": 0}])])
    def test_single_unit_processor(self, prog_file, util_info):
        """Test simulating a program on a single-unit processor.

        `self` is this test case.
        `prog_file` is the program file.
        `util_info` is the expected utilization information.

        """
        cpu = test_utils.read_proc_file(
            "processors", "singleALUUnitProcessor.yaml")
        capabilities = processor_utils.get_abilities(cpu)
        assert processor.simulate(
            test_utils.compile_prog(prog_file, test_utils.read_isa_file(
                "singleInstructionISA.yaml", capabilities)), cpu) == util_info


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])

if __name__ == '__main__':
    main()
