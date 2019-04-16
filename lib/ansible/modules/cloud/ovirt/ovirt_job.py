#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_job
short_description: Module to manage tags in oVirt/RHV
version_added: "2.9"
author: "Ondra Machacek (@machacekondra)"
description:
    - "This module manage tags in oVirt/RHV. It can also manage assignments
       of those tags to entities."
options:
    id:
        description:
            - "ID of the tag to manage."
    name:
        description:
            - "Name of the tag to manage."
        required: true
    state:
        description:
            - "Should the tag be present/absent."
            - "C(Note): I(attached) and I(detached) states are supported since version 2.4."
        choices: ['present', 'absent']
        default: present
    description:
        description:
            - "Description of the tag to manage."
    parent:
        description:
            - "Name of the parent tag."
    vms:
        description:
            - "List of the VMs names, which should have assigned this tag."
    hosts:
        description:
            - "List of the hosts names, which should have assigned this tag."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create(if not exists) and assign tag to vms vm1 and vm2:
- ovirt_tag:
    name: mytag
    vms:
      - vm1
      - vm2

# Attach a tag to VM 'vm3', keeping the rest already attached tags on VM:
- ovirt_tag:
    name: mytag
    state: attached
    vms:
      - vm3

'''

RETURN = '''
id:
    description: ID of the tag which is managed
    returned: On success if tag is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
job:
    description: "Dictionary of all the tag attributes. Tag attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/job."
    returned: On success if tag is found.
    type: dict
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    get_id_by_name,
    ovirt_full_argument_spec,
)


class JobsModule(BaseModule):

    def build_entity(self):
        return otypes.Job(
                description=self._module.params['description'],
                status=otypes.JobStatus.STARTED,
                external=True,
                auto_cleared=True
                #steps=[otypes.Step(type=otypes.StepStatus.UNKNOWN) for step in self._module.params('steps') ] if self._module.params('steps') is not None else None
            )

def attach_steps(module, entity_id, jobs_service):
    # Attach NICs to VM, if specified:
    steps_service = jobs_service.job_service(entity_id).steps_service()
    if module.params.get('steps'):
        for step in module.params.get('steps'):
            step_entity = get_entity(steps_service, step.get('description')) 
            if step_entity is None:
     #           if not self._module.check_mode:
                    steps_service.add(
                        otypes.Step(
                            description=step.get('description'),
                            type=otypes.StepEnum.UNKNOWN,
                            job=otypes.Job(
                                id=entity_id
                            ),
                            status=otypes.StepStatus.STARTED,
                            external=True,
                        )
                    )
    #            self.changed = True
            elif step.get('state') == 'absent':
                steps_service.step_service(step_entity.id).end(status=otypes.StepStatus.FINISHED,succeeded=True)


def get_entity(jobs_service, description):
    all_jobs = jobs_service.list()
    for job in all_jobs:
        if job.description == description and job.status != "finished":
            return job
    

def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        description=dict(default=None),
        status=dict(default=None),
        steps=dict(default=None, type='list'),
        
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        jobs_service = connection.system_service().jobs_service()
        jobs_module = JobsModule(
            connection=connection,
            module=module,
            service=jobs_service,
        )

        state = module.params['state']
        job = get_entity(jobs_service, module.params['description'])
        if state == 'present':
            ret = jobs_module.create(entity=job)
            attach_steps(module,ret.get('job').get('id'),jobs_service)
        elif state == 'absent':
            jobs_service.job_service(job.id).end(status=otypes.JobStatus.FINISHED)
            ret ={
                'changed': True,
                'id': getattr(job, 'id', None),
            }

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
