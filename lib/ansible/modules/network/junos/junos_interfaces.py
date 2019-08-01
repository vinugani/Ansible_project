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
The module file for junos_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: junos_interfaces
version_added: 2.9
short_description: Manages interface attributes of Juniper Junos OS network devices.
description: This module manages the interfaces on Juniper Junos OS network devices.
author: Ganesh Nalawade (@ganeshrn)
options:
  config:
    description: The provided configuration
    type: list
    suboptions:
      name:
        description:
        - Full name of interface, e.g. ge-0/0/0.
        type: str
        required: True
      description:
        description:
        - Interface description.
        type: str
      duplex:
        description:
        - Interface link status. Applicable for Ethernet interfaces only, either in half duplex,
          full duplex or in automatic state which negotiates the duplex automatically.
        type: str
        choices: ['automatic', 'full-duplex', 'half-duplex']
      enable:
        default: True
        description:
        - Administrative state of the interface.
        - Set the value to C(true) to administratively enable the interface or C(false) to disable it.
        type: bool
      hold_time:
        description:
        - The hold time for given interface name.
        type: dict
        suboptions:
          down:
            description:
            - The link down hold time in milliseconds.
            type: int
          up:
            description:
            - The link up hold time in milliseconds.
            type: int
      mtu:
        description:
        - MTU for a specific interface.
        - Applicable for Ethernet interfaces only.
        type: int
      speed:
        description:
        - Interface link speed. Applicable for Ethernet interfaces only.
        type: int
  state:
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged
    description:
    - The state the configuration should be left in
    type: str
requirements:
  - ncclient (>=v0.6.4)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 18.4R1.
  - This module works with connection C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).

"""
EXAMPLES = """
# Using deleted

# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "Configured by Ansible-1";
#    speed 1g;
#    mtu 1800
# }
# ge-0/0/2 {
#    description "Configured by Ansible-2";
#    ether-options {
#        auto-negotiation;
#    }
# }

- name: "Delete given options for the interface (Note: This won't delete the interface itself if any other values are configured for interface)"
  junos_interfaces:
    config:
      - name: ge-0/0/1
        description: 'Configured by Ansible-1'
        speed: 1g
        mtu: 1800
      - name: ge-0/0/2
        description: 'Configured by Ansible -2'
    state: deleted

# After state:
# ------------
# user@junos01# show interfaces
# ge-0/0/2 {
#    ether-options {
#        auto-negotiation;
#    }
# }


# Using merged

# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "test interface";
#    speed 1g;
# }

- name: "Merge provided configuration with device configuration (default operation is merge)"
  junos_interfaces:
    config:
      - name: ge-0/0/1
        description: 'Configured by Ansible-1'
        enable: True
        mtu: 1800
      - name: ge-0/0/2
        description: 'Configured by Ansible-2'
        enable: False
    state: merged

# After state:
# ------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "Configured by Ansible-1";
#    speed 1g;
#    mtu 1800
# }
# ge-0/0/2 {
#    disable;
#    description "Configured by Ansible-2";
# }


# Using overriden

# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "Configured by Ansible-1";
#    speed 1g;
#    mtu 1800
# }
# ge-0/0/2 {
#    disable;
#    description "Configured by Ansible-2";
#    ether-options {
#        auto-negotiation;
#    }
# }
# ge-0/0/11 {
#    description "Configured by Ansible-11";
# }

- name: "Override device configuration of all interfaces with provided configuration"
  junos_interfaces:
    config:
      - name: ge-0/0/2
        description: 'Configured by Ansible-2'
        enable: False
        mtu: 2800
      - name: ge-0/0/3
        description: 'Configured by Ansible-3'
    state: overriden

# After state:
# ------------
# user@junos01# show interfaces
# ge-0/0/2 {
#    disable;
#    description "Configured by Ansible-2";
#    mtu 2800
# }
# ge-0/0/3 {
#    description "Configured by Ansible-3";
# }


# Using replaced

# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "Configured by Ansible-1";
#    speed 1g;
#    mtu 1800
# }
# ge-0/0/2 {
#    disable;
#    mtu 1800;
#    speed 1g;
#    description "Configured by Ansible-2";
#    ether-options {
#        auto-negotiation;
#    }
# }
# ge-0/0/11 {
#    description "Configured by Ansible-11";
# }

- name: "Replaces device configuration of listed interfaces with provided configuration"
  junos_interfaces:
    config:
      - name: ge-0/0/2
        description: 'Configured by Ansible-2'
        enable: False
        mtu: 2800
      - name: ge-0/0/3
        description: 'Configured by Ansible-3'
    state: replaced

# After state:
# ------------
# user@junos01# show interfaces
# ge-0/0/1 {
#    description "Configured by Ansible-1";
#    speed 1g;
#    mtu 1800
# }
# ge-0/0/2 {
#    disable;
#    description "Configured by Ansible-2";
#    mtu 2800
# }
# ge-0/0/3 {
#    description "Configured by Ansible-3";
# }
# ge-0/0/11 {
#    description "Configured by Ansible-11";
# }


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
xml:
  description: The set of xml rpc payload pushed to the remote device.
  returned: always
  type: list
  sample: ['xml 1', 'xml 2', 'xml 3']
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network.junos.config.interfaces.interfaces import Interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=InterfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
