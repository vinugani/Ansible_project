#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: qnos_reboot
version_added: "2.9"
author: "Mark Yang (@QCT)"
short_description: Reboot a Quanta QNOS network device.
description:
  - Reboot a Quanta QNOS network device.
extends_documentation_fragment: qnos
options:
  confirm:
    description:
      - Safeguard boolean. Set to true if you're sure you want to reboot.
    required: true
    default: null
    choices: ['yes', 'no']
  save:
    description:
      - Safeguard boolean. Set to true if you're sure to save the running-
        config to the startup-config at rebooting.
    required: true
    default: null
    choices: ['yes', 'no']
"""

EXAMPLES = """
- name: reboot the device
  qnos_reboot:
    confirm: yes
    save: no
"""

RETURN = """
rebooted:
    description: Whether the device was instructed to reboot.
    returned: success
    type: boolean
    sample: true
"""
import re
import time

from ansible.module_utils.network.qnos.qnos import run_reload
from ansible.module_utils.network.qnos.qnos import qnos_argument_spec
from ansible.module_utils.network.qnos.qnos import check_args as qnos_check_args
from ansible.module_utils.network.qnos.qnos import send_data
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.connection import exec_command
from ansible.module_utils.six import string_types

def check_args(module, warnings):

    qnos_check_args(module, warnings)
    confirm = module.params['confirm']
    if not confirm:
        module.fail_json(msg='confirm must be set to yes for this '
                             'module to work.')

    save = module.params['save']
    if save=='':
        module.fail_json(msg='save must be explicitly set to yes or no for this '
                             'module to work.')


def main():
    """ main entry point for module execution
    """
    commands = list()
    responses = list()
    argument_spec = dict(
        # this argument is deprecated (2.2) in favor of setting match: none
        # it will be removed in a future version
        response=dict(),
        confirm=dict(required=True, type='bool'),
        save=dict(required=True, type='bool'),
        config=dict(),
        defaults=dict(type='bool', default=False),
    )

    argument_spec.update(qnos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                 supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    changed = False
    rebooted = False
    save = module.params['save']

    responses = run_reload(module,save=save)

    result['response'] = responses
    changed = save
    rebooted = True

    result['changed'] = changed
    result['rebooted'] = rebooted

    module.exit_json(**result)


if __name__ == '__main__':
    main()
