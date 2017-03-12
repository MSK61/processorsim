#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests processor services"""

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
# file:         test_processor.py
#
# function:     processor service tests
#
# description:  tests processor and ISA loading
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.0 build 89833, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#
# notes:        This is a private program.
#
############################################################

from itertools import imap
from os.path import join
import src_importer
import unittest
from yaml import load
src_importer.add_src_path()
import processor_utils
from processor_utils import load_proc_desc

class ProcDescTest(unittest.TestCase):

    """Test case for loading processor description"""

    _DATA_DIR_NAME = "data"

    def test_processor_with_two_connected_functional_units(self):
        """Test loading a processor with two functional units.

        `self` is this test case.

        """
        in_file = "twoConnectedUnitsProcessor.yaml"
        with open(join(self._DATA_DIR_NAME, in_file)) as proc_file:
            proc_desc = load_proc_desc(load(proc_file))
        unit_idx_map = dict(imap(lambda entry: (entry[1].model.name, entry[0]),
                                 enumerate(proc_desc)))
        self.assertEqual(
            frozenset(imap(lambda unit: unit_idx_map[unit.name],
                           proc_desc[0].predecessors)), frozenset([1]))

    def test_single_functional_unit_processor(self):
        """Test loading a single function unit processor.

        `self` is this test case.

        """
        in_file = "singleUnitProcessor.yaml"
        with open(join(self._DATA_DIR_NAME, in_file)) as proc_file:
            self.assertEqual(
                load_proc_desc(load(proc_file)), [processor_utils.FuncUnit(
                    processor_utils.UnitModel("fullSys", 1, []), [ ])])

def main():
    """entry point for running test in this module"""
    unittest.main()

if __name__ == '__main__':
    main()
