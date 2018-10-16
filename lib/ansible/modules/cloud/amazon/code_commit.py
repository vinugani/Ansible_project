#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: code_commit
version_added: "2.8"
short_description: Manage repositories in AWS CodeCommit
description:
  - Supports creation and deletion of CodeCommit repositories.
  - See U(https://aws.amazon.com/codecommit/) for more information about CodeCommit.
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.6

options:
  name:
    description:
      - name of repository.
    required: true
  comment:
    description:
      - description or comment of repository.
    required: false
  state:
    description:
      - Specifies the state of repository.
    required: true
    choices: [ 'present', 'absent' ]

extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
repository_metadata:
  description: ""
  returned: always
  type: complex
  contains:
    account_id:
      description: ""
      returned: always
      type: string
      sample: "268342293637"
    arn:
      description: ""
      returned: always
      type: string
      sample: "arn:aws:codecommit:ap-northeast-1:268342293637:username"
    clone_url_http:
      description: ""
      returned: always
      type: string
      sample: "https://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/reponame"
    clone_url_ssh:
      description: ""
      returned: always
      type: string
      sample: "ssh://git-codecommit.ap-northeast-1.amazonaws.com/v1/repos/reponame"
    creation_date:
      description: ""
      returned: always
      type: string
      sample: "2018-10-16T13:21:41.261000+09:00"
    last_modified_date:
      description: ""
      returned: always
      type: string
      sample: "2018-10-16T13:21:41.261000+09:00"
    repository_description:
      description: ""
      returned: always
      type: string
      sample: "test from ptux"
    repository_id:
      description: ""
      returned: always
      type: string
      sample: "e62a5c54-i879-497b-b62f-9f99e4ebfk8e"
    repository_name:
      description: ""
      returned: always
      type: string
      sample: "reponame"

response_metadata:
  description: ""
  returned: always
  type: complex
  contains:
    http_headers:
      description: ""
      returned: always
      type: complex
    http_status_code:
      description: ""
      returned: always
      type: string
      sample: "200"
    request_id:
      description: ""
      returned: always
      type: string
      sample: "fb49cfca-d0fa-11e8-85cb-b3cc4b5045ef"
    retry_attempts:
      description: ""
      returned: always
      type: string
      sample: "0"

'''

EXAMPLES = '''
# Create a new repository
- code_commit:
    name: repo
    state: present
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


class CodeCommit(object):
    def __init__(self, module=None):
        self._module = module
        self._client = self._module.client('codecommit')
        self._check_mode = self._module.check_mode

    def process(self):
        result = dict(changed=False)

        if self._module.params['state'] == 'present' and not self._repository_exists():
            if not self._module.check_mode:
                result = self._create_repository()
            result['changed'] = True
        if self._module.params['state'] == 'absent' and self._repository_exists():
            if not self._module.check_mode:
                result = self._delete_repository()
            result['changed'] = True
        return result

    def _repository_exists(self):
        try:
            paginator = self._client.get_paginator('list_repositories')
            for page in paginator.paginate():
                repositories = page['repositories']
                for item in repositories:
                    if self._module.params['name'] in item.values():
                        return True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't get repository")
        return False

    def _create_repository(self):
        try:
            result = self._client.create_repository(
                repositoryName=self._module.params['name'],
                repositoryDescription=self._module.params['comment']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't create repository")
        return result

    def _delete_repository(self):
        try:
            result = self._client.delete_repository(
                repositoryName=self._module.params['name']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't delete repository")
        return result


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], required=True),
        comment=dict(default='')
    )

    ansible_aws_module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    code_commit = CodeCommit(module=ansible_aws_module)
    result = code_commit.process()
    ansible_aws_module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
