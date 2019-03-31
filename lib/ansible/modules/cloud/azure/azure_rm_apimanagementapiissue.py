#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_apimanagementapiissue
version_added: '2.9'
short_description: Manage Azure ApiIssue instance.
description:
  - 'Create, update and delete instance of Azure ApiIssue.'
options:
  resource_group_name:
    description:
      - The name of the resource group.
  service_name:
    description:
      - The name of the API Management service.
  api_id:
    description:
      - >-
        API identifier. Must be unique in the current API Management service
        instance.
  issue_id:
    description:
      - >-
        Issue identifier. Must be unique in the current API Management service
        instance.
  properties:
    description:
      - Properties of the Issue.
    suboptions:
      title:
        description:
          - The issue title.
        required: true
      description:
        description:
          - Text describing the issue.
        required: true
      user_id:
        description:
          - A resource identifier for the user created the issue.
        required: true
  _if-_match:
    description:
      - >-
        ETag of the Issue Entity. ETag should match the current entity state
        from the header response of the GET request or it should be * for
        unconditional update.
  state:
    description:
      - Assert the state of the ApiIssue.
      - >-
        Use C(present) to create or update an ApiIssue and C(absent) to delete
        it.
    default: present
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: ApiManagementCreateApiIssue
  azure_rm_apimanagementapiissue:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    issueId: 57d2ef278aa04f0ad01d6cdc
    apiId: 57d1f7558aa04f15146d9d8a
    properties:
      title: New API issue
      description: New API issue description
      createdDate: '2018-02-01T22:21:20.467Z'
      state: open
      userId: >-
        /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group
        }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/users/{{
        user_name }}

'''

RETURN = '''
{}

'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
from msrestazure.azure_exceptions import CloudError


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMApiIssue(AzureRMModuleBase):
    """Configuration class for an Azure RM ApiIssue resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str'
            ),
            service_name=dict(
                type='str'
            ),
            api_id=dict(
                type='str'
            ),
            issue_id=dict(
                type='str'
            ),
            properties=dict(
                type='dict'
            ),
            _if-_match=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group_name = None
        self.service_name = None
        self.api_id = None
        self.issue_id = None
        self._if-_match = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-01-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMApiIssue, self).__init__(derived_arg_spec=self.module_arg_spec,
                                              supports_check_mode=True,
                                              supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "properties":
                    self.body["properties"] = kwargs[key]

        self.adjust_parameters()

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.ApiManagement' +
                    '/service' +
                    '/{{ service_name }}' +
                    '/apis' +
                    '/{{ apis_name }}' +
                    '/issues' +
                    '/{{ issue_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ service_name }}', self.service_name)
        self.url = self.url.replace('{{ apis_name }}', self.apis_name)
        self.url = self.url.replace('{{ issue_name }}', self.issue_name)

        old_response = self.get_apiissue()

        if not old_response:
            self.log("ApiIssue instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('ApiIssue instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if ApiIssue instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the ApiIssue instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_apiissue()

            # if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('ApiIssue instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_apiissue()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_apiissue():
                time.sleep(20)
        else:
            self.log('ApiIssue instance unchanged')
            self.results['changed'] = False
            response = old_response


        return self.results

    def adjust_parameters(self):
if self.parameters.get('properties', None) is not None:

    def rename_key(self, d, old_name, new_name):
        old_value = d.get(old_name, None)
        if old_value is not None:
            d.pop(old_name, None)
            d[new_name] = old_value

    def create_update_apiissue(self):
        '''
        Creates or updates ApiIssue with the specified configuration.

        :return: deserialized ApiIssue instance state dictionary
        '''
        # self.log('Creating / Updating the ApiIssue instance {0}'.format(self.))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code)
            else:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code)
            # implement poller in another way
            # if isinstance(response, AzureOperationPoller):
            #    response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the ApiIssue instance.')
            self.fail('Error creating the ApiIssue instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_apiissue(self):
        '''
        Deletes specified ApiIssue instance in the specified subscription and resource group.

        :return: True
        '''
        # self.log('Deleting the ApiIssue instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
        except CloudError as e:
            self.log('Error attempting to delete the ApiIssue instance.')
            self.fail('Error deleting the ApiIssue instance: {0}'.format(str(e)))

        return True

    def get_apiissue(self):
        '''
        Gets the properties of the specified ApiIssue.

        :return: deserialized ApiIssue instance state dictionary
        '''
        # self.log('Checking if the ApiIssue instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
            found = True
            self.log("Response : {0}".format(response))
            # self.log("ApiIssue instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ApiIssue instance.')
        if found is True:
            return response

        return False


def main():
    """Main execution"""
    AzureRMApiIssue()


if __name__ == '__main__':
    main()
