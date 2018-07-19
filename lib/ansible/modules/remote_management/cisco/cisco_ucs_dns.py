#!/usr/bin/python

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cisco_ucs_dns
short_description: Configures DNS on a Cisco UCS server.
version_added: "2.4"
description:
   -  Configures DNS on a Cisco UCS server.
options:
    state:
        description:
         - if C(present), adds DNS server
         - if C(absent), removes DNS server
        choices: ['present', 'absent']
        default: "present"
    name:
        description: ip address of dns server
        required: true
    descr:
        description: description of server

requirements:
    - 'ucsmsdk'
    - 'ucsm_apis'
    - 'python2 >= 2.7.9 or python3 >= 3.2'
    - 'openssl version >= 1.0.1'

extends_documentation_fragment:
    - cisco_ucs

author: "Cisco Systems Inc(ucs-python@cisco.com)"
'''


EXAMPLES = '''
- name: "Add DNS Server"
  cisco_ucs_dns:
    name: "10.10.10.10"
    descr: "description"
    state: "present"
    ucs_ip: "192.168.1.1"
    ucs_username: "admin"
    ucs_password: "password"
'''

RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule


def _argument_mo():
    return dict(
        name=dict(required=True, type='str'),
        descr=dict(type='str'),
    )


def _argument_custom():
    return dict(
        state=dict(default="present",
                   choices=['present', 'absent'],
                   type='str'),
    )


def _argument_connection():
    return dict(
        # UcsHandle
        ucs_server=dict(type='dict'),

        # Ucs server credentials
        ucs_ip=dict(type='str'),
        ucs_username=dict(default="admin", type='str'),
        ucs_password=dict(type='str', no_log=True),
        ucs_port=dict(default=None),
        ucs_secure=dict(default=None),
        ucs_proxy=dict(default=None)
    )


def _ansible_module_create():
    argument_spec = dict()
    argument_spec.update(_argument_mo())
    argument_spec.update(_argument_custom())
    argument_spec.update(_argument_connection())

    return AnsibleModule(argument_spec,
                         supports_check_mode=True)


def _get_mo_params(params):
    args = {}
    for key in _argument_mo():
        if params.get(key) is None:
            continue
        args[key] = params.get(key)
    return args


def setup_dns(server, module):
    from ucsm_apis.admin.dns import dns_server_add
    from ucsm_apis.admin.dns import dns_server_remove
    from ucsm_apis.admin.dns import dns_server_exists

    ansible = module.params
    args_mo = _get_mo_params(ansible)
    exists, mo = dns_server_exists(handle=server, **args_mo)

    if ansible["state"] == "present":
        if module.check_mode or exists:
            return not exists
        dns_server_add(handle=server, **args_mo)
    else:
        if module.check_mode or not exists:
            return exists
        dns_server_remove(server, mo.name)
    return True


def setup(server, module):
    result = {}
    err = False

    try:
        result["changed"] = setup_dns(server, module)
    except Exception as e:
        err = True
        result["msg"] = "setup error: %s " % str(e)
        result["changed"] = False

    return result, err


def main():
    from ansible.module_utils.cisco_ucs import UcsConnection

    module = _ansible_module_create()
    conn = UcsConnection(module)
    server = conn.login()
    result, err = setup(server, module)
    conn.logout()
    if err:
        module.fail_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
