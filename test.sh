#!/usr/bin/env bash
############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023, 2024 Mohammed El-Afifi
# This file is part of processorSim.
#
# processorSim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# processorSim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with processorSim.  If not, see <http://www.gnu.org/licenses/>.
#
# program:      processor simulator
#
# file:         test.sh
#
# function:     main test driver
#
# description:  runs all tests
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.86.1, Fedora release 39 (Thirty Nine)
#
# notes:        This is a private program.
#
############################################################
set -e
# just running a sample test module to make sure test modules are executable on
# their own
tests/test_containers.py
pytest --cov src --flake8 --pylint $*
black --check .
PYRIGHT_PYTHON_IGNORE_WARNINGS=1 pyright
cd src
pytest -m "mypy or pylint" --mypy --pylint $*
