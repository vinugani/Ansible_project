#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: iosxr_netconf
version_added: "2.5"
author: "Kedar Kekan (@kedarX)"
short_description: Configures NetConf sub-system service on Cisco IOS-XR devices
description:
  - This module provides an abstraction that enables and configures
    the netconf system service running on Cisco IOS-XR Software.
    This module can be used to easily enable the Netconf API. Netconf provides
    a programmatic interface for working with configuration and state
    resources as defined in RFC 6242.
extends_documentation_fragment: iosxr
options:
  netconf_port:
    description:
      - This argument specifies the port the netconf service should
        listen on for SSH connections.  The default port as defined
        in RFC 6242 is 830.
    required: false
    default: 830
    aliases: ['listens_on']
  netconf_vrf:
    description:
      - netconf vrf name
    required: false
    default: none
  state:
    description:
      - Specifies the state of the C(iosxr_netconf) resource on
        the remote device.  If the I(state) argument is set to
        I(present) the netconf service will be configured.  If the
        I(state) argument is set to I(absent) the netconf service
        will be removed from the configuration.
    required: false
    default: present
    choices: ['present', 'absent']
notes:
  - Tested against Cisco IOS XR Software, Version 6.1.2
"""

EXAMPLES = """
- name: enable netconf service on port 830
  iosxr_netconf:
    listens_on: 830
    state: present

- name: disable netconf service
  iosxr_netconf:
    state: absent
"""

RETURN = """
commands:
  description: Returns the command sent to the remote device
  returned: when changed is True
  type: str
  sample: 'ssh server netconf port 830'
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.six import iteritems

USE_PERSISTENT_CONNECTION = True


def map_obj_to_commands(updates, module):
    want, have = updates
    commands = list()

    if want['state'] == 'absent':
        if have['state'] == 'present':
            commands.append('no netconf-yang agent ssh')

            if 'netconf_port' in have:
                commands.append('no ssh server netconf port %s' % have['netconf_port'])
            if 'netconf_vrf' in have:
                commands.append('no ssh server netconf vrf %s' % have['netconf_vrf'])
    else:
        if have['state'] == 'absent':
            commands.append('netconf-yang agent ssh')

        if want['netconf_port'] != have.get('netconf_port'):
            commands.append(
                'ssh server netconf port %s' % want['netconf_port']
            )
        if want['netconf_vrf'] != have.get('netconf_vrf'):
            commands.append(
                'ssh server netconf vrf %s' % want['netconf_vrf']
            )

    return commands


def parse_vrf(config):
    match = re.search(r'vrf (\w+)', config)
    if match:
        return match.group(1)


def parse_port(config):
    match = re.search(r'port (\d+)', config)
    if match:
        return int(match.group(1))


def map_config_to_obj(module):
    obj = {'state': 'absent'}

    netconf_config = get_config(module, flags=['netconf-yang agent'])

    ssh_config = get_config(module, flags=['ssh server'])
    ssh_config = [config_line for config_line in (line.strip() for line in ssh_config.splitlines()) if config_line]

    for config in ssh_config:
        if 'netconf port' in config:
            obj.update({'netconf_port': parse_port(config)})
        if 'netconf vrf' in config:
            obj.update({'netconf_vrf': parse_vrf(config)})
    if 'ssh' in netconf_config or 'netconf_port' in obj or 'netconf_vrf' in obj:
        obj.update({'state': 'present'})

    if 'ssh' in netconf_config and 'netconf_port' not in obj:
        obj.update({'netconf_port': 830})
    return obj


def validate_netconf_port(value, module):
    if not 1 <= value <= 65535:
        module.fail_json(msg='netconf_port must be between 1 and 65535')


def map_params_to_obj(module):
    obj = {
        'netconf_port': module.params['netconf_port'],
        'netconf_vrf': module.params['netconf_vrf'],
        'state': module.params['state']
    }

    for key, value in iteritems(obj):
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(value, module)

    return obj


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        netconf_port=dict(type='int', default=830, aliases=['listens_on']),
        netconf_vrf=dict(aliases=['vrf']),
        state=dict(default='present', choices=['present', 'absent']),
    )
    argument_spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
            exec_command(module, 'exit')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
