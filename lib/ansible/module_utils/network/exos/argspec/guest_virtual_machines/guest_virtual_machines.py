#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the exos_guest_virtual_machines module
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type


class Guest_virtual_machinesArgs(object):  # pylint: disable=R0903
    """The arg spec for the exos_guest_virtual_machines module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
            'config': {
                'elements': 'dict',
                'options': {
                    'auto_start': {'type': 'bool'},
                    'forceful': {'type': 'bool'},
                    'image': {'type': 'str'},
                    'memory_size': {'type': 'int'},
                    'name': {'type': 'str'},
                    'num_cores': {'type': 'int'},
                    'operational_state': {
                        'choices': ['started',
                                    'stopped',
                                    'restarted'],
                        'type': 'str'},
                    'virtual_ports': {
                        'options': {
                            'name': {'type': 'str'},
                            'port': {'type': 'str'},
                            'type': {'choices': ['vtd',
                                                 'sriov',
                                                 'bridge'],
                                     'type': 'str'},
                            'vlan': {'type': 'int'}},
                        'type': 'dict'},
                    'vnc': {
                        'options': {
                            'enabled': {'type': 'bool'},
                            'port': {'type': 'int'}},
                        'type': 'dict'}},
                'type': 'list'},
 'state': {
     'choices': ['merged', 'replaced', 'overridden', 'deleted'],
     'default': 'merged',
     'type': 'str'}}  # pylint: disable=C0301
