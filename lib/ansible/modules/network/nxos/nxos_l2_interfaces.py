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
The module file for nxos_l2_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: nxos_l2_interfaces
version_added: 2.9
short_description: Manages Layer-2 Interfaces attributes of NX-OS Interfaces
description: This module manages Layer-2 interfaces attributes of NX-OS Interfaces.
author: Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOS 7.3.(0)D1(1) on VIRL
options:
  config:
    description: A dictionary of Layer-2 interface options
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of interface, i.e. Ethernet1/1.
        type: str
        required: true
      access:
        description:
          - Switchport mode access command to configure the interface as a
            Layer-2 access.
        type: dict
        suboptions:
          vlan:
            description:
            - Configure given VLAN in access port. It's used as the access
              VLAN ID.
            type: int
      trunk:
        description:
          - Switchport mode trunk command to configure the interface as a
            Layer-2 trunk.
        type: dict
        suboptions:
          native_vlan:
            description:
              - Native VLAN to be configured in trunk port. It is used as the
                trunk native VLAN ID.
            type: int
          allowed_vlans:
            description:
              - List of allowed VLANs in a given trunk port. These are the only
                VLANs that will be configured on the trunk.
            type: str
      mode:
        description:
        - Mode in which interface needs to be configured.
        - Access mode is not shown in interface facts, so idempotency will not be
          maintained for switchport mode access.
        version_added: '2.10'
        type: str
        choices: ['access', 'trunk']

  state:
    description:
      - The state of the configuration after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
    default: merged
"""
EXAMPLES = """
# Using merged

# Before state:
# -------------
#
# interface Ethernet1/1
#   switchport access vlan 20
# interface Ethernet1/2
#   switchport trunk native vlan 20
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config

- name: Merge provided configuration with device configuration.
  nxos_l2_interfaces:
    config:
      - name: Ethernet1/1
        trunk:
          native_vlan: 10
          allowed_vlans: 2,4,15
      - name: Ethernet1/2
        access:
          vlan: 30
    state: merged

# After state:
# ------------
#
# interface Ethernet1/1
#   switchport trunk native vlan 10
#   switchport trunk allowed vlans 2,4,15
# interface Ethernet1/2
#   switchport access vlan 30
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config


# Using replaced

# Before state:
# -------------
#
# interface Ethernet1/1
#   switchport access vlan 20
# interface Ethernet1/2
#   switchport trunk native vlan 20
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config

- name: Replace device configuration of specified L2 interfaces with provided configuration.
  nxos_l2_interfaces:
    config:
      - name: Ethernet1/1
        trunk:
          native_vlan: 20
          trunk_vlans: 5-10, 15
    state: replaced

# After state:
# ------------
#
# interface Ethernet1/1
#   switchport trunk native vlan 20
#   switchport trunk allowed vlan 5-10,15
# interface Ethernet1/2
#   switchport trunk native vlan 20
#   switchport mode trunk
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config


# Using overridden

# Before state:
# -------------
#
# interface Ethernet1/1
#   switchport access vlan 20
# interface Ethernet1/2
#   switchport trunk native vlan 20
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config

- name: Override device configuration of all L2 interfaces on device with provided configuration.
  nxos_l2_interfaces:
    config:
      - name: Ethernet1/2
        access:
          vlan: 30
    state: overridden

# After state:
# ------------
#
# interface Ethernet1/1
# interface Ethernet1/2
#   switchport access vlan 30
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config


# Using deleted

# Before state:
# -------------
#
# interface Ethernet1/1
#   switchport access vlan 20
# interface Ethernet1/2
#   switchport trunk native vlan 20
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config

- name: Delete L2 attributes of given interfaces (Note This won't delete the interface itself).
  nxos_l2_interfaces:
    config:
      - name: Ethernet1/1
      - name: Ethernet1/2
    state: deleted

# After state:
# ------------
#
# interface Ethernet1/1
# interface Ethernet1/2
# interface mgmt0
#   ip address dhcp
#   ipv6 address auto-config


"""
RETURN = """
before:
  description: The configuration as structured data prior to module invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The configuration as structured data after module completion.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.network.nxos.config.l2_interfaces.l2_interfaces import L2_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=L2_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = L2_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
