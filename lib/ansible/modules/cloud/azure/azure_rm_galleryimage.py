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
module: azure_rm_galleryimage
version_added: '2.9'
short_description: Manage Azure GalleryImage instance.
description:
  - 'Create, update and delete instance of Azure GalleryImage.'
options:
  resource_group:
    description:
      - The name of the resource group.
    required: true
  gallery_name:
    description:
      - >-
        The name of the Shared Image Gallery in which the Image Definition is to
        be created.
    required: true
  name:
    description:
      - >-
        The name of the gallery Image Definition to be created or updated. The
        allowed characters are alphabets and numbers with dots, dashes, and
        periods allowed in the middle. The maximum length is 80 characters.
    required: true
  gallery_image:
    description:
      - Parameters supplied to the create or update gallery image operation.
    required: true
  location:
    description:
      - Resource location
    required: true
  description:
    description:
      - >-
        The description of this gallery Image Definition resource. This property
        is updatable.
  eula:
    description:
      - The Eula agreement for the gallery Image Definition.
  privacy_statement_uri:
    description:
      - The privacy statement uri.
  release_note_uri:
    description:
      - The release note uri.
  os_type:
    description:
      - >-
        This property allows you to specify the type of the OS that is included
        in the disk when creating a VM from a managed image. <br><br> Possible
        values are: <br><br> **Windows** <br><br> **Linux**
    required: true
  os_state:
    description:
      - The allowed values for OS State are 'Generalized'.
    required: true
  end_of_life_date:
    description:
      - >-
        The end of life date of the gallery Image Definition. This property can
        be used for decommissioning purposes. This property is updatable.
  identifier:
    description:
      - undefined
    required: true
    suboptions:
      publisher:
        description:
          - The name of the gallery Image Definition publisher.
        required: true
      offer:
        description:
          - The name of the gallery Image Definition offer.
        required: true
      sku:
        description:
          - The name of the gallery Image Definition SKU.
        required: true
  recommended:
    description:
      - undefined
    suboptions:
      v_cpus:
        description:
          - undefined
        suboptions:
          min:
            description:
              - The minimum number of the resource.
          max:
            description:
              - The maximum number of the resource.
      memory:
        description:
          - undefined
        suboptions:
          min:
            description:
              - The minimum number of the resource.
          max:
            description:
              - The maximum number of the resource.
  disallowed:
    description:
      - undefined
    suboptions:
      disk_types:
        description:
          - A list of disk types.
        type: list
  purchase_plan:
    description:
      - undefined
    suboptions:
      name:
        description:
          - The plan ID.
      publisher:
        description:
          - The publisher ID.
      product:
        description:
          - The product ID.
  state:
    description:
      - Assert the state of the GalleryImage.
      - >-
        Use C(present) to create or update an GalleryImage and C(absent) to
        delete it.
    default: present
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
  - azure_tags
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: Create or update a simple gallery image.
  azure_rm_galleryimage:
    resource_group: myResourceGroup
    gallery_name: myGallery
    name: myImage
    gallery_image:
      location: West US
      properties:
        osType: Windows
        osState: Generalized
        identifier:
          publisher: myPublisherName
          offer: myOfferName
          sku: mySkuName
- name: Delete a gallery image.
  azure_rm_galleryimage:
    resource_group: myResourceGroup
    gallery_name: myGallery
    name: myImage
    state: absent

'''

RETURN = '''
id:
  description:
    - Resource Id
  returned: always
  type: str
  sample: null
name:
  description:
    - Resource name
  returned: always
  type: str
  sample: null
type:
  description:
    - Resource type
  returned: always
  type: str
  sample: null

'''

import time
import json
import re
from ansible.module_utils.azure_rm_common_ext import AzureRMModuleBaseExt
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
from msrestazure.azure_exceptions import CloudError


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMGalleryImages(AzureRMModuleBaseExt):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                updatable=False,
                disposition='resourceGroupName',
                required=True
            ),
            gallery_name=dict(
                type='str',
                updatable=False,
                disposition='galleryName',
                required=True
            ),
            name=dict(
                type='str',
                updatable=False,
                disposition='galleryImageName',
                required=True
            ),
            location=dict(
                type='str',
                updatable=False,
                disposition='/',
                required=True
            ),
            description=dict(
                type='str',
                disposition='/properties/*'
            ),
            eula=dict(
                type='str',
                disposition='/properties/*'
            ),
            privacy_statement_uri=dict(
                type='str',
                disposition='/properties/privacyStatementUri'
            ),
            release_note_uri=dict(
                type='str',
                disposition='/properties/releaseNoteUri'
            ),
            os_type=dict(
                type='str',
                disposition='/properties/osType',
                choices=['Windows',
                         'Linux'],
                required=True
            ),
            os_state=dict(
                type='str',
                disposition='/properties/osState',
                choices=['Generalized',
                         'Specialized'],
                required=True
            ),
            end_of_life_date=dict(
                type='datetime',
                disposition='/properties/endOfLifeDate'
            ),
            identifier=dict(
                type='dict',
                disposition='/properties/*',
                required=True,
                options=dict(
                    publisher=dict(
                        type='str',
                        required=True
                    ),
                    offer=dict(
                        type='str',
                        required=True
                    ),
                    sku=dict(
                        type='str',
                        required=True
                    )
                )
            ),
            recommended=dict(
                type='dict',
                disposition='/properties/*',
                options=dict(
                    v_cpus=dict(
                        type='dict',
                        disposition='vCPUs',
                        options=dict(
                            min=dict(
                                type='number'
                            ),
                            max=dict(
                                type='number'
                            )
                        )
                    ),
                    memory=dict(
                        type='dict',
                        options=dict(
                            min=dict(
                                type='number'
                            ),
                            max=dict(
                                type='number'
                            )
                        )
                    )
                )
            ),
            disallowed=dict(
                type='dict',
                disposition='/properties/*',
                options=dict(
                    disk_types=dict(
                        type='list',
                        disposition='diskTypes'
                    )
                )
            ),
            purchase_plan=dict(
                type='dict',
                disposition='/properties/purchasePlan',
                options=dict(
                    name=dict(
                        type='str'
                    ),
                    publisher=dict(
                        type='str'
                    ),
                    product=dict(
                        type='str'
                    )
                )
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.gallery_name = None
        self.name = None
        self.gallery_image = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 201, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2019-03-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMGalleryImages, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                   supports_check_mode=True,
                                                   supports_tags=True)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.body[key] = kwargs[key]

        self.inflate_parameters(self.module_arg_spec, self.body, 0)

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if 'location' not in self.body:
            self.body['location'] = resource_group.location

        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Compute' +
                    '/galleries' +
                    '/{{ gallery_name }}' +
                    '/images' +
                    '/{{ image_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ gallery_name }}', self.gallery_name)
        self.url = self.url.replace('{{ image_name }}', self.name)

        old_response = self.get_resource()

        if not old_response:
            self.log("GalleryImage instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('GalleryImage instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            else:
                modifiers = {}
                self.create_compare_modifiers(self.module_arg_spec, '', modifiers)
                self.results['modifiers'] = modifiers
                self.results['compare'] = []
                if not self.default_compare(modifiers, self.body, old_response, '', self.results):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the GalleryImage instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_resource()

            # if not old_response:
            self.results['changed'] = True
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('GalleryImage instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_resource()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_resource():
                time.sleep(20)
        else:
            self.log('GalleryImage instance unchanged')
            self.results['changed'] = False
            response = old_response

        if response:
           self.results["id"] = response["id"]
           self.results["name"] = response["name"]
           self.results["type"] = response["type"]

        return self.results

    def create_update_resource(self):
        # self.log('Creating / Updating the GalleryImage instance {0}'.format(self.))

        try:
            response = self.mgmt_client.query(self.url,
                                              'PUT',
                                              self.query_parameters,
                                              self.header_parameters,
                                              self.body,
                                              self.status_code,
                                              600,
                                              30)
        except CloudError as exc:
            self.log('Error attempting to create the GalleryImage instance.')
            self.fail('Error creating the GalleryImage instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_resource(self):
        # self.log('Deleting the GalleryImage instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
        except CloudError as e:
            self.log('Error attempting to delete the GalleryImage instance.')
            self.fail('Error deleting the GalleryImage instance: {0}'.format(str(e)))

        return True

    def get_resource(self):
        # self.log('Checking if the GalleryImage instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            found = True
            self.log("Response : {0}".format(response))
            # self.log("GalleryImage instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the GalleryImage instance.')
        if found is True:
            return response

        return False


def main():
    AzureRMGalleryImages()


if __name__ == '__main__':
    main()
