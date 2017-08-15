#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_snmptrapprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of SnmpTrapProfile Avi RESTful Object
description:
    - This module is used to configure SnmpTrapProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    name:
        description:
            - A user-friendly name of the snmp trap configuration.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    trap_servers:
        description:
            - The ip address or hostname of the snmp trap destination server.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the snmp trap profile object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create SnmpTrapProfile object
  avi_snmptrapprofile:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_snmptrapprofile
"""

RETURN = '''
obj:
    description: SnmpTrapProfile (api/snmptrapprofile) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        name=dict(type='str', required=True),
        tenant_ref=dict(type='str',),
        trap_servers=dict(type='list',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'snmptrapprofile',
                           set([]))

if __name__ == '__main__':
    main()
