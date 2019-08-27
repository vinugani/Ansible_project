#!/usr/bin/python
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
The module file for vyos_lldp_global
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network'
}

DOCUMENTATION = """
---
module: vyos_lldp_global
version_added: 2.9
short_description: Manage link layer discovery protocol (LLDP) attributes on VyOS devices..
description: This module manages link layer discovery protocol (LLDP) attributes on VyOS devices.
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
author:
   - Rohit Thakur (@rohitthakur2590)
options:
  config:
    description: The provided link layer discovery protocol (LLDP) configuration.
    type: dict
    suboptions:
      enable:
        description:
          - This argument is a boolean value to enable or disable LLDP.
        type: bool
      address:
        description:
          - This argument defines management-address.
        type: str
      snmp:
        description:
          - This argument enable the SNMP queries to LLDP database.
        type: str
      legacy_protocols:
        description:
          - List of the supported legacy protocols.
        type: list
        choices:
          - cdp
          - edp
          - fdp
          - sonmp
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
    - merged
    - replaced
    - deleted
    default: merged
"""
EXAMPLES = """
# Using merged
#
# Before state:
# -------------
#
# vyos@vyos:~$ show configuration commands|grep lldp
# vyos@vyos:~$
#
- name: Merge provided configuration with device configuration
  vyos_lldp_global:
    config:
      legacy_protocols:
        - 'fdp'
        - 'cdp'
      snmp: 'enable'
      address: 192.0.2.11
    state: merged
#
#
# ------------------------
# Module Execution Results
# ------------------------
#
# "before": []
#
# "commands": [
#        "set service lldp legacy-protocols fdp",
#        "set service lldp legacy-protocols cdp",
#        "set service lldp snmp enable",
#        "set service lldp management-address '192.0.2.11'"
#    ]
#
# "after": [
#        {
#            "snmp": "enable"
#        },
#        {
#            "address": "192.0.2.11"
#        },
#        {
#            "legacy_protocols": [
#                "cdp",
#                "fdp"
#            ]
#        }
#        {
#            "enable": true
#        }
#    ]
#
# After state:
# -------------
#
# set service lldp legacy-protocols cdp
# set service lldp legacy-protocols fdp
# set service lldp management-address '192.0.2.11'
# set service lldp snmp enable


# Using replaced
#
# Before state:
# -------------
#
# vyos@vyos:~$ show configuration commands | grep lldp
# set service lldp legacy-protocols cdp
# set service lldp legacy-protocols fdp
# set service lldp management-address '192.0.2.11'
# set service lldp snmp enable
#
- name: Replace device configurations with provided configurations
  vyos_lldp_global:
    config:
      legacy_protocols:
        - 'edp'
        - 'sonmp'
        - 'cdp'
      address: 192.0.2.14
    state: replaced
#
#
# ------------------------
# Module Execution Results
# ------------------------
#
#
# "before": [
#        {
#            "snmp": "enable"
#        },
#        {
#            "address": "192.0.2.11"
#        },
#        {
#            "legacy_protocols": [
#                "cdp",
#                "fdp"
#            ]
#        }
#        {
#            "enable": true
#        }
#    ]
# "commands": [
#        "delete service lldp snmp",
#        "delete service lldp legacy-protocols fdp",
#        "set service lldp management-address '192.0.2.14'",
#        "set service lldp legacy-protocols edp",
#        "set service lldp legacy-protocols sonmp"
#    ]
#
# "after": [
#        {
#            "address": "192.0.2.14"
#        },
#        {
#            "legacy_protocols": [
#                "cdp",
#                "edp",
#                "sonmp"
#            ]
#        }
#        {
#            "enable": true
#        }
#    ]
#
# After state:
# -------------
#
# vyos@vyos:~$ show configuration commands|grep lldp
# set service lldp legacy-protocols cdp
# set service lldp legacy-protocols edp
# set service lldp legacy-protocols sonmp
# set service lldp management-address '192.0.2.14'


# Using deleted
#
# Before state
# -------------
# vyos@vyos:~$ show configuration commands|grep lldp
# set service lldp legacy-protocols cdp
# set service lldp legacy-protocols edp
# set service lldp legacy-protocols sonmp
# set service lldp management-address '192.0.2.14'
#
- name: Delete attributes of given lldp service (This won't delete the LLDP service itself)
  vyos_lldp_global:
    config:
    state: deleted
#
#
# ------------------------
# Module Execution Results
# ------------------------
#
# "before": [
#        {
#            "address": "192.0.2.14"
#        },
#        {
#            "legacy_protocols": [
#                "cdp",
#                "edp",
#                "sonmp"
#            ]
#        }
#        {
#            "enable": true
#        }
#    ]
#
#  "commands": [
#       "delete service lldp management-address",
#        "delete service lldp legacy-protocols"
#    ]
#
# "after": [
#        {
#            "enable": true
#        }
#          ]
#
# After state
# ------------
# vyos@vyos:~$ show configuration commands | grep lldp
# set service lldp


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample:
    - set service lldp legacy-protocols sonmp
    - set service lldp management-address '192.0.2.14'
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.vyos.argspec.lldp_global.lldp_global import Lldp_globalArgs
from ansible.module_utils.network.vyos.config.lldp_global.lldp_global import Lldp_global


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    required_if = [('state', 'merged', ('config',)),
                   ('state', 'replaced', ('config',))]
    module = AnsibleModule(argument_spec=Lldp_globalArgs.argument_spec, required_if=required_if,
                           supports_check_mode=True)

    result = Lldp_global(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
