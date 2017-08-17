# -*- coding: utf-8 -*-

"""tests utilities"""

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
# file:         test_utils.py
#
# function:     testing utilities
#
# description:  auxiliary test utilities
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Fedora release 25 (Twenty Five)
#               Komodo IDE, version 10.2.1 build 89853, python 2.7.13,
#               Ubuntu 17.04
#
# notes:        This is a private program.
#
############################################################

from os.path import join
import test_env
import processor_utils
import program_utils
import yaml
TEST_DATA_DIR = join(test_env.TEST_DIR, "data")


class ValInStrCheck:

    """Verification point for checking a string contains a value"""

    def __init__(self, real_val, exp_val):
        """Create a verification point.

        `self` is this verification point.
        `real_val` is the actual value.
        `exp_val` is the expected value.
        The constructor asserts that the real and expected values match.

        """
        assert real_val == exp_val
        self._value = exp_val

    def check(self, msg, start_index):
        """Check that the message contains the associated value.

        `self` is this verification point.
        `msg` is the message to be checked.
        `start_index` is the index to start searching after.
        The method returns the index of the associated value in the
        given message after the specified index.

        """
        start_index = msg.find(str(self._value), start_index + 1)
        assert start_index >= 0
        return start_index


def chk_error(verify_points, error):
    """Check the specifications of an error.

    `verify_points` are the verification points to assess.
    `error` is the error to assess whose message.
    The function checks the given verification points and that they're
    contained in the error message.

    """
    error = str(error)
    idx = -1

    for cur_point in verify_points:
        idx = cur_point.check(error, idx)


def compile_prog(prog_file, isa):
    """Compile a file using the given instruction set.

    `prog_file` is the program file.
    `isa` is the instruction set.

    """
    return program_utils.compile_program(read_prog_file(prog_file), isa)


def read_isa_file(file_name, capabilities):
    """Read an instruction set file.

    `file_name` is the instruction set file name.
    `capabilities` are supported capabilities.
    The function returns the instruction set mapping.

    """
    test_dir = "ISA"
    return processor_utils.load_isa(
        _load_yaml(test_dir, file_name), capabilities)


def read_proc_file(proc_dir, file_name):
    """Read a processor description file.

    `proc_dir` is the directory containing the processor description file.
    `file_name` is the processor description file name.
    The function returns the processor description.

    """
    return processor_utils.load_proc_desc(_load_yaml(proc_dir, file_name))


def read_prog_file(file_name):
    """Read a program file.

    `file_name` is the program file name.
    The function returns the loaded program.

    """
    test_dir = "programs"
    return program_utils.read_program(join(TEST_DATA_DIR, test_dir, file_name))


def _load_yaml(test_dir, file_name):
    """Read a test YAML file.

    `test_dir` is the directory containing the YAML file.
    `file_name` is the YAML file name.
    The function returns the loaded YAML object.

    """
    with open(join(TEST_DATA_DIR, test_dir, file_name)) as test_file:
        return yaml.load(test_file)
