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

import os.path
import test_utils
import processor
import processor_utils
import program_utils
import unittest


class SimTest(unittest.TestCase):

    """Test case for program simulation"""

    def test_empty_program(self):
        """Test simulating an empty program.

        `self` is this test case.

        """
        cpu = test_utils.read_file("processors", "singleUnitALUProcessor.yaml")
        prog = program_utils.compile_program(
            program_utils.read_program(
                os.path.join(test_utils.TEST_DATA_DIR, "programs",
                             "empty.asm")), processor_utils.load_isa(
                test_utils.load_yaml("ISA", "emptyISA.yaml"),
                processor_utils.get_abilities(cpu)))
        assert processor.simulate(prog, cpu) == []


def main():
    """entry point for running test in this module"""
    unittest.main()

if __name__ == '__main__':
    main()
