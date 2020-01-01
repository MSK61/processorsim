#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor abilities service"""

############################################################
#
# Copyright 2017, 2019, 2020 Mohammed El-Afifi
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
# file:         test_abilities.py
#
# function:     processor ability extraction service tests
#
# description:  tests processor ability extraction
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.41.1, python 3.7.5, Fedora release
#               31 (Thirty One)
#
# notes:        This is a private program.
#
############################################################

import pytest

import test_utils
import processor_utils
import str_utils


class TestAbilities:

    """Test case for extracting processor capabilities"""

    @pytest.mark.parametrize("in_file, capabilities", [
        ("singleALUProcessor.yaml", ["ALU"]), ("singleMemUnitProcessor.yaml", [
            "MEM"]), ("dualCoreALUMemProcessor.yaml", ["ALU", "MEM"]),
        ("twoConnectedUnitsProcessor.yaml", ["ALU"])])
    def test_abilities(self, in_file, capabilities):
        """Test extracting abilities from a processor.

        `self` is this test case.
        `in_file` is the processor description file.
        `capabilities` are the processor capabilities.

        """
        assert processor_utils.get_abilities(
            test_utils.read_proc_file("processors", in_file)) == frozenset(
                map(str_utils.ICaseString, capabilities))


def main():
    """entry point for running test in this module"""
    pytest.main([__file__])


if __name__ == '__main__':
    main()
