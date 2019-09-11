#!/usr/bin/env bash
############################################################
#
# Copyright 2017, 2019 Mohammed El-Afifi
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
# environment:  Visual Studdio Code 1.38.0, Fedora release 30 (Thirty)
#
# notes:        This is a private program.
#
############################################################
python3 -m pytest --codestyle --cov src --flakes $*
