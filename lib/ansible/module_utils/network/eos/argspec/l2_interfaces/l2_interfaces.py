# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

##############################################
#                 WARNING                    #
##############################################
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
##############################################

"""
The arg spec for the eos_l2_interfaces module
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class L2_interfacesArgs(object):
    """The arg spec for the eos_l2_interfaces module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        'config': {
            'elements': 'dict',
            'options': {
                'access': {'options': {'vlan': {'type': 'int'}},
                    'type': 'dict'},
                'name': {'required': True, 'type': 'str'
                'trunk': {'options': {'native_vlan': {'type': 'int'}, 'trunk_allowed_vlans': {'type': 'list'}},
                    'type': 'dict'}},
            'type': 'list'},
        'state': {'default': 'merged', 'choices': ['merged', 'replaced', 'overridden', 'deleted'], 'required': False, 'type': 'str'}
    }
