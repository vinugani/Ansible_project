#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_role
short_description: Module to manage roles in oVirt/RHV
version_added: "2.9"
author: "Martin Necas (@mnecas)"
description:
    - "Module to manage roles in oVirt/RHV."
options:
    name:
        description:
            - "Name of the role to manage."
    id:
        description:
            - "ID of the role to manage."
    state:
        description:
            - "Should the template be present/absent.
        choices: ['present', 'absent']
        default: present
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- ovirt_role:
    mutable: true
    name: "test2"
    administrative: true
    permits:
        - name: "manipulate_permissions"
        - name: "create_instance"


'''

RETURN = '''


'''

import time
import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    convert_to_bytes,
    create_connection,
    equal,
    get_dict_of_struct,
    get_link_name,
    get_id_by_name,
    ovirt_full_argument_spec,
    search_by_attributes,
    search_by_name,
)


class RoleModule(BaseModule):
    def build_entity(self):
        return otypes.Role(
            id=self.param('id'),
            name=self.param('name'),
            mutable=self.param('mutable') if self.param('mutable') else None,
            administrative=self.param('administrative') if self.param('administrative') else None,
            #user=otypes.User(
            #    name=self.param('user')
            #) if self.param('user') else None,
        )

    def update_check(self, entity):
        return (
            equal(self.param('mutable'), entity.mutable) and
            equal(self.param('administrative'), entity.administrative)
            #equal(self.param('user'), entity.user.name)
        )


    def post_present(self, entity_id):
        self.changed = self.__set_permits(entity_id)


    def _find_permit_id(self, permit, all_permits):
        for el in all_permits:
            if el.name == permit.get('name'):
                return el.id

    def __set_permits(self, entity_id):
        permits_service = self._service.service(entity_id).permits_service()
        current_permits = permits_service.list()
        all_permits = self._connection.system_service().cluster_levels_service().level_service('4.3').get().permits
        #clear all permits
        for permit in current_permits:
            permits_service.permit_service(permit.id).remove()
        #add new permits 
        for new_permit in self.param('permits'):
            permits_service.add(
                otypes.Permit(
                    administrative=True,
                    id=self._find_permit_id(new_permit, all_permits)
                ) 
            )
        #compare 
        if current_permits == self._service.service(entity_id).permits_service().list():
            return False
        return True
        

def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        id=dict(default=None),
        name=dict(default=None),
        user=dict(default=None),
        mutable=dict(default=True,type='bool'),
        administrative=dict(default=False, type='bool'),
        permits=dict(type='list', default=[]),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['id', 'name']],
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        roles_service = connection.system_service().roles_service()
        roles_module = RoleModule(
            connection=connection,
            module=module,
            service=roles_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = roles_module.create()
            roles_module.post_present(ret['id'])
            ret['changed'] = roles_module.changed
        elif state == 'absent':
            ret = roles_module.remove()
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
