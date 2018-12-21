#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_tag
short_description: Manage VMware tags
description:
- This module can be used to create / delete / update VMware tags.
- Tag feature is introduced in vSphere 6 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
version_added: '2.6'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
- vCloud Suite SDK
options:
    tag_name:
      description:
      - The name of tag to manage.
      required: True
    tag_description:
      description:
      - The tag description.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      - Process of updating tag only allows description change.
      required: False
      default: ''
    category_id:
      description:
      - The unique ID generated by vCenter should be used to.
      - User can get this unique ID from facts module.
      required: False
    state:
      description:
      - The state of tag.
      - If set to C(present) and tag does not exists, then tag is created.
      - If set to C(present) and tag exists, then tag is updated.
      - If set to C(absent) and tag exists, then tag is deleted.
      - If set to C(absent) and tag does not exists, no action is taken.
      required: False
      default: 'present'
      choices: [ 'present', 'absent' ]
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Create a tag
  vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    category_id: 'urn:vmomi:InventoryServiceCategory:e785088d-6981-4b1c-9fb8-1100c3e1f742:GLOBAL'
    tag_name: Sample_Tag_0002
    tag_description: Sample Description
    state: present
  delegate_to: localhost

- name: Update tag description
  vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: Sample_Tag_0002
    tag_description: Some fancy description
    state: present
  delegate_to: localhost

- name: Delete tag
  vmware_tag:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    tag_name: Sample_Tag_0002
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
results:
  description: dictionary of tag metadata
  returned: on success
  type: dict
  sample: {
        "msg": "Tag 'Sample_Tag_0002' created.",
        "tag_id": "urn:vmomi:InventoryServiceTag:bff91819-f529-43c9-80ca-1c9dfda09441:GLOBAL"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_rest_client import VmwareRestClient
try:
    from com.vmware.cis.tagging_client import Tag
except ImportError:
    pass


class VmwareTag(VmwareRestClient):
    def __init__(self, module):
        super(VmwareTag, self).__init__(module)
        self.tag_service = Tag(self.connect)
        self.global_tags = dict()
        self.tag_name = self.params.get('tag_name')
        self.get_all_tags()

    def ensure_state(self):
        """
        Function to manage internal states of tags

        """
        desired_state = self.params.get('state')
        states = {
            'present': {
                'present': self.state_update_tag,
                'absent': self.state_create_tag,
            },
            'absent': {
                'present': self.state_delete_tag,
                'absent': self.state_unchanged,
            }
        }
        states[desired_state][self.check_tag_status()]()

    def state_create_tag(self):
        """
        Function to create tag

        """
        tag_spec = self.tag_service.CreateSpec()
        tag_spec.name = self.tag_name
        tag_spec.description = self.params.get('tag_description')
        category_id = self.params.get('category_id', None)
        if category_id is None:
            self.module.fail_json(msg="'category_id' is required parameter while creating tag.")
        tag_spec.category_id = category_id
        tag_id = self.tag_service.create(tag_spec)
        if tag_id:
            self.module.exit_json(changed=True,
                                  results=dict(msg="Tag '%s' created." % tag_spec.name,
                                               tag_id=tag_id))
        self.module.exit_json(changed=False,
                              results=dict(msg="No tag created", tag_id=''))

    def state_unchanged(self):
        """
        Function to return unchanged state

        """
        self.module.exit_json(changed=False)

    def state_update_tag(self):
        """
        Function to update tag

        """
        changed = False
        results = dict(msg="Tag %s is unchanged." % self.tag_name,
                       tag_id=self.global_tags[self.tag_name]['tag_id'])
        tag_update_spec = self.tag_service.UpdateSpec()
        tag_desc = self.global_tags[self.tag_name]['tag_description']
        desired_tag_desc = self.params.get('tag_description')
        if tag_desc != desired_tag_desc:
            tag_update_spec.setDescription = desired_tag_desc
            results['msg'] = 'Tag %s updated.' % self.tag_name
            changed = True

        self.module.exit_json(changed=changed, results=results)

    def state_delete_tag(self):
        """
        Function to delete tag

        """
        tag_id = self.global_tags[self.tag_name]['tag_id']
        self.tag_service.delete(tag_id=tag_id)
        self.module.exit_json(changed=True,
                              results=dict(msg="Tag '%s' deleted." % self.tag_name,
                                           tag_id=tag_id))

    def check_tag_status(self):
        """
        Function to check if tag exists or not
        Returns: 'present' if tag found, else 'absent'

        """
        if self.tag_name in self.global_tags:
            return 'present'
        else:
            return 'absent'

    def get_all_tags(self):
        """
        Function to retrieve all tag information

        """
        for tag in self.tag_service.list():
            tag_obj = self.tag_service.get(tag)
            self.global_tags[tag_obj.name] = dict(tag_description=tag_obj.description,
                                                  tag_used_by=tag_obj.used_by,
                                                  tag_category_id=tag_obj.category_id,
                                                  tag_id=tag_obj.id
                                                  )


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        tag_name=dict(type='str', required=True),
        tag_description=dict(type='str', default='', required=False),
        category_id=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], default='present', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    vmware_tag = VmwareTag(module)
    vmware_tag.ensure_state()


if __name__ == '__main__':
    main()
