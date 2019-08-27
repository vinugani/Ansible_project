#!/usr/bin/python
# -*- coding: utf-8 -*-
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
module: iam_saml_federation
version_added: "2.9"
short_description: maintain iam saml federation configuration.
requirements:
    - boto3
description:
    - Provides a mechanism to manage AWS IAM SAML Identity Federation providers (create/update/delete metadata).
options:
    name:
        description:
            - The name of the provider to create.
        required: true
    saml_metadata_document:
        description:
            - The XML document generated by an identity provider (IdP) that supports SAML 2.0.
    state:
        description:
            - Whether to create or delete identity provider. If 'present' is specified it will attempt to update the identity provider matching the name field.
        default: present
        choices: [ "present", "absent" ]
extends_documentation_fragment:
    - aws
author:
    - Tony (@axc450)
    - Aidan Rowe (@aidan-)
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# It is assumed that their matching environment variables are set.
# Creates a new iam saml identity provider if not present
- name: saml provider
  iam_saml_federation:
      name: example1
      # the > below opens an indented block, so no escaping/quoting is needed when in the indentation level under this key
      saml_metadata_document: >
          <?xml version="1.0"?>...
          <md:EntityDescriptor
# Creates a new iam saml identity provider if not present
- name: saml provider
  iam_saml_federation:
      name: example2
      saml_metadata_document: "{{ item }}"
  with_file: /path/to/idp/metdata.xml
# Removes iam saml identity provider
- name: remove saml provider
  iam_saml_federation:
      name: example3
      state: absent
'''

RETURN = '''
saml_provider:
    description: Details of the SAML Identity Provider that was created/modified.
    type: complex
    returned: present
    contains:
        arn:
            description: The ARN of the identity provider.
            type: str
            returned: present
            sample: "arn:aws:iam::123456789012:saml-provider/my_saml_provider"
        metadata_document:
            description: The XML metadata document that includes information about an identity provider.
            type: str
            returned: present
        create_date:
            description: The date and time when the SAML provider was created in ISO 8601 date-time format.
            type: str
            returned: present
            sample: "2017-02-08T04:36:28+00:00"
        expire_date:
            description: The expiration date and time for the SAML provider in ISO 8601 date-time format.
            type: str
            returned: present
            sample: "2017-02-08T04:36:28+00:00"
'''

try:
    import boto3
    import botocore.exceptions

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, aws_common_argument_spec, get_aws_connection_info, boto3_conn


class SAMLProviderManager:
    """Handles SAML Identity Provider configuration"""

    def __init__(self, module, **aws_connection_params):
        self.module = module
        self.aws_connection_params = aws_connection_params

        try:
            self.conn = boto3_conn(module, conn_type='client', resource='iam', **self.aws_connection_params)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=str(e))

    # use retry decorator for boto3 calls
    @AWSRetry.backoff(tries=3, delay=5)
    def _list_saml_providers(self):
        return self.conn.list_saml_providers()

    @AWSRetry.backoff(tries=3, delay=5)
    def _get_saml_provider(self, arn):
        return self.conn.get_saml_provider(SAMLProviderArn=arn)

    @AWSRetry.backoff(tries=3, delay=5)
    def _update_saml_provider(self, arn, metadata):
        return self.conn.update_saml_provider(SAMLProviderArn=arn, SAMLMetadataDocument=metadata)

    @AWSRetry.backoff(tries=3, delay=5)
    def _create_saml_provider(self, metadata, name):
        return self.conn.create_saml_provider(SAMLMetadataDocument=metadata, Name=name)

    @AWSRetry.backoff(tries=3, delay=5)
    def _delete_saml_provider(self, arn):
        return self.conn.delete_saml_provider(SAMLProviderArn=arn)

    def _get_provider_arn(self, name):
        providers = self._list_saml_providers()
        for p in providers['SAMLProviderList']:
            provider_name = p['Arn'].split('/', 1)[1]
            if name == provider_name:
                return p['Arn']

        return None

    def create_or_update_saml_provider(self, name, metadata):
        if not metadata:
            self.module.fail_json(msg="saml_metadata_document must be defined for present state")

        res = {'changed': False}
        try:
            arn = self._get_provider_arn(name)
        except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as e:
            res['msg'] = str(e)
            self.module.fail_json(**res)

        if arn:  # see if metadata needs updating
            try:
                resp = self._get_saml_provider(arn)
            except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as e:
                res['msg'] = str(e)
                res['debug'] = [arn]
                self.module.fail_json(**res)

            if metadata.strip() != resp['SAMLMetadataDocument'].strip():
                # provider needs updating
                res['changed'] = True
                if not self.module.check_mode:
                    try:
                        resp = self._update_saml_provider(arn, metadata)
                        res['saml_provider'] = self._build_res(resp['SAMLProviderArn'])
                    except botocore.exceptions.ClientError as e:
                        res['msg'] = str(e)
                        res['debug'] = [arn, metadata]
                        self.module.fail_json(**res)

        else:  # create
            res['changed'] = True
            if not self.module.check_mode:
                try:
                    resp = self._create_saml_provider(metadata, name)
                    res['saml_provider'] = self._build_res(resp['SAMLProviderArn'])
                except botocore.exceptions.ClientError as e:
                    res['msg'] = str(e)
                    res['debug'] = [name, metadata]
                    self.module.fail_json(**res)

        self.module.exit_json(**res)

    def delete_saml_provider(self, name):
        res = {'changed': False}
        try:
            arn = self._get_provider_arn(name)
        except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as e:
            res['msg'] = str(e)
            self.module.fail_json(**res)

        if arn:  # delete
            res['changed'] = True
            if not self.module.check_mode:
                try:
                    self._delete_saml_provider(arn)
                except botocore.exceptions.ClientError as e:
                    res['msg'] = str(e)
                    res['debug'] = [arn]
                    self.module.fail_json(**res)

        self.module.exit_json(**res)

    def _build_res(self, arn):
        saml_provider = self._get_saml_provider(arn)
        return {
            "arn": arn,
            "metadata_document": saml_provider["SAMLMetadataDocument"],
            "create_date": saml_provider["CreateDate"].isoformat(),
            "expire_date": saml_provider["ValidUntil"].isoformat()
        }


def main():
    argument_spec = dict(
        name=dict(required=True),
        saml_metadata_document=dict(default=None, required=False),
        state=dict(default='present', required=False, choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    name = module.params['name']
    state = module.params.get('state')
    saml_metadata_document = module.params.get('saml_metadata_document')

    sp_man = SAMLProviderManager(module, **aws_connect_kwargs)

    if state == 'present':
        sp_man.create_or_update_saml_provider(name, saml_metadata_document)
    elif state == 'absent':
        sp_man.delete_saml_provider(name)


if __name__ == '__main__':
    main()
