#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the iosxr facts module.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class FactsArgs(object):  # pylint: disable=R0903
    """ The arg spec for the iosxr facts module
    """

    def __init__(self, **kwargs):
        pass

    choices = [
        'all',
        'lacp',
        '!lacp',
        'lacp_interfaces',
        '!lacp_interfaces'
    ]

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(choices=choices, type='list'),
    }
