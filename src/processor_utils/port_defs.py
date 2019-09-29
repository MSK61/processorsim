# -*- coding: utf-8 -*-

"""port definitions"""

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
# file:         port_defs.py
#
# function:     get_in_ports and get_out_ports
#
# description:  port definitions
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studdio Code 1.38.1, python 3.7.4, Fedora release
#               30 (Thirty)
#
# notes:        This is a private program.
#
############################################################


class PortGroup:

    """Port group information"""

    def __init__(self, processor):
        """Extract port information from the given processor.

        `self` is this port group.
        `processor` is the processor to extract port group information
                    from.

        """
        self._in_ports, self._out_ports = map(lambda port_getter: tuple(
            port_getter(processor)), [get_in_ports, get_out_ports])

    @property
    def in_ports(self):
        """Input ports

        `self` is this port group.

        """
        return self._in_ports

    @property
    def out_ports(self):
        """Output ports

        `self` is this port group.

        """
        return self._out_ports


def get_in_ports(processor):
    """Find the input ports.

    `processor` is the processor to find whose input ports.
    The function returns an iterator over the processor input ports.

    """
    return _get_ports(processor.in_degree())


def get_out_ports(processor):
    """Find the output ports.

    `processor` is the processor to find whose output ports.
    The function returns an iterator over the processor output ports.

    """
    return _get_ports(processor.out_degree())


def _get_ports(degrees):
    """Find the ports with respect to the given degrees.

    `degrees` are the degrees of all units.
    A port is a unit with zero degree.

    """
    return (unit for unit, deg in degrees if not deg)
