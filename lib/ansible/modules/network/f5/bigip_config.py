#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_config
short_description: Manage BIG-IP configuration sections
description:
  - Manages a BIG-IP configuration by allowing TMSH commands that
    modify running configuration, or merge SCF formatted files into
    the running configuration. Additionally, this module is of
    significant importance because it allows you to save your running
    configuration to disk. Since the F5 module only manipulate running
    configuration, it is important that you utilize this module to save
    that running config.
version_added: 2.4
options:
  save:
    description:
      - The C(save) argument instructs the module to save the
        running-config to startup-config.
      - This operation is performed after any changes are made to the
        current running config. If no changes are made, the configuration
        is still saved to the startup config.
      - This option will always cause the module to return changed.
    type: bool
    default: yes
  reset:
    description:
      - Loads the default configuration on the device.
      - If this option is specified, the default configuration will be
        loaded before any commands or other provided configuration is run.
    type: bool
    default: no
  merge_content:
    description:
      - Loads the specified configuration that you want to merge into
        the running configuration. This is equivalent to using the
        C(tmsh) command C(load sys config from-terminal merge).
      - If you need to read configuration from a file or template, use
        Ansible's C(file) or C(template) lookup plugins respectively.
  verify:
    description:
      - Validates the specified configuration to see whether they are
        valid to replace the running configuration.
      - The running configuration will not be changed.
      - When this parameter is set to C(yes), no change will be reported
        by the module.
    type: bool
    default: no
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Save the running configuration of the BIG-IP
  bigip_config:
    save: yes
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: Reset the BIG-IP configuration, for example, to RMA the device
  bigip_config:
    reset: yes
    save: yes
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: Load an SCF configuration
  bigip_config:
    merge_content: "{{ lookup('file', '/path/to/config.scf') }}"
    server: lb.mydomain.com
    password: secret
    user: admin
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
stdout:
  description: The set of responses from the options
  returned: always
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
'''

import os
import tempfile

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Parameters(AnsibleF5Parameters):
    returnables = ['stdout', 'stdout_lines']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(params=changed)

    def _to_lines(self, stdout):
        lines = list()
        for item in stdout:
            if isinstance(item, str):
                item = str(item).split('\n')
            lines.append(item)
        return lines

    def exec_module(self):
        result = {}
        try:
            changed = self.execute()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.changes.to_return())
        result.update(dict(changed=changed))
        return result

    def execute(self):
        responses = []
        if self.want.reset:
            response = self.reset()
            responses.append(response)

        if self.want.merge_content:
            if self.want.verify:
                response = self.merge(verify=True)
                responses.append(response)
            else:
                response = self.merge(verify=False)
                responses.append(response)

        if self.want.save:
            response = self.save()
            responses.append(response)

        self._detect_errors(responses)
        changes = {
            'stdout': responses,
            'stdout_lines': self._to_lines(responses)
        }
        self.changes = Parameters(params=changes)
        if self.want.verify:
            return False
        return True

    def _detect_errors(self, stdout):
        errors = [
            'Unexpected Error:'
        ]

        msg = [x for x in stdout for y in errors if y in x]
        if msg:
            # Error only contains the lines that include the error
            raise F5ModuleError(' '.join(msg))

    def reset(self):
        if self.module.check_mode:
            return True
        return self.reset_device()

    def reset_device(self):
        command = 'tmsh load sys config default'
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            return str(output.commandResult)
        return None

    def merge(self, verify=True):
        temp_name = next(tempfile._get_candidate_names())
        remote_path = "/var/config/rest/downloads/{0}".format(temp_name)
        temp_path = '/tmp/' + temp_name

        if self.module.check_mode:
            return True

        self.upload_to_device(temp_name)
        self.move_on_device(remote_path)
        response = self.merge_on_device(
            remote_path=temp_path, verify=verify
        )
        self.remove_temporary_file(remote_path=temp_path)
        return response

    def merge_on_device(self, remote_path, verify=True):
        result = None

        command = 'tmsh load sys config file {0} merge'.format(
            remote_path
        )
        if verify:
            command += ' verify'

        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            result = str(output.commandResult)
        return result

    def remove_temporary_file(self, remote_path):
        self.client.api.tm.util.unix_rm.exec_cmd(
            'run',
            utilCmdArgs=remote_path
        )

    def move_on_device(self, remote_path):
        self.client.api.tm.util.unix_mv.exec_cmd(
            'run',
            utilCmdArgs='{0} /tmp/{1}'.format(
                remote_path, os.path.basename(remote_path)
            )
        )

    def upload_to_device(self, temp_name):
        template = StringIO(self.want.merge_content)
        upload = self.client.api.shared.file_transfer.uploads
        upload.upload_stringio(template, temp_name)

    def save(self):
        if self.module.check_mode:
            return True
        return self.save_on_device()

    def save_on_device(self):
        result = None
        command = 'tmsh save sys config'
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        if hasattr(output, 'commandResult'):
            result = str(output.commandResult)
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            reset=dict(
                type='bool',
                default=False
            ),
            merge_content=dict(),
            verify=dict(
                type='bool',
                default=False
            ),
            save=dict(
                type='bool',
                default='yes'
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
