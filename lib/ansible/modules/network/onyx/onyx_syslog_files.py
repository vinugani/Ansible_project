#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: onyx_syslog_files
version_added: "2.10"
author: "Anas Shami (@anass)"
short_description: Configure file management syslog module
description:
  - This module provides declarative management of syslog
    on Mellanox ONYX network devices.
notes:
options:
    debug:
      description:
        - Configure settings for debug log files
      type: bool
      default: False
    delete_group:
      description:
        - Delete certain log files
      choices: ['current', 'oldest']
      type: str
    rotation:
      description:
        - rotation related attributes
      type: dict
      suboptions:
        frequency:
          description:
          - Rotate log files on a fixed time-based schedule
          choices: ['daily', 'weekly', 'monthly']
          type: str
        force:
            description:
            - force an immediate rotation of log files
            type: bool
        max_num:
            description:
            - Sepcify max_num of old log files to keep
            type: int
        size:
            description:
            - Rotate files when they pass max size
            type: float
        size_pct:
            description:
            - Rotatoe files when they pass percent of HD
            type: float
    upload_url:
        description:
          - upload local log files to remote host (ftp, scp, sftp, tftp)
        type: str
    upload_file:
        description:
           - Upload compressed log file (current or filename)
        type: str
"""

EXAMPLES = """
- name: syslog delete old files
- onyx_syslog_files:
    delete_group: oldest
- name: syslog upload file
- onyx_syslog_files:
    upload_url: scp://username:password@hostnamepath/filename
    upload_file: current
- name: syslog rotation force, frequency and max number
- onyx_syslog_files:
    rotation:
        force: true
        max_num: 30
        frequency: daily
        size: 128
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device.
    returned: always
    type: list
    sample:
        - logging files delete current
        - logging files rotate criteria
        - logging files upload current url
"""
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxSyslogFilesModule(BaseOnyxModule):
    MAX_FILES = 999999
    URL_REGEX = re.compile(
        r'^(ftp|scp|ftps):\/\/[a-z0-9\.]*:(.*)@(.*):([a-zA-Z\/\/])*$')
    FREQUANCIES = ['daily', 'weekly', 'monthly']
    ROTATION_KEYS = ['frequency', 'max_num', 'size', 'size_pct', 'force']
    ROTATION_CMDS = {'size': 'logging {0} rotation criteria size {1}',
                     'frequency': 'logging {0} rotation criteria frequency {1}',
                     'max_num': 'logging {0} rotation max-num {1}',
                     'size_pct': 'logging {0} rotation criteria size-pct {1}',
                     'force': 'logging {0} rotation force'}

    def init_module(self):
        """" Ansible module initialization
        """
        rotation_spec = dict(frequency=dict(choices=self.FREQUANCIES),
                             max_num=dict(type="int"),
                             force=dict(type="bool"),
                             size=dict(type="float"),
                             size_pct=dict(type="float"))

        element_spec = dict(delete_group=dict(choices=['oldest', 'current']),
                            rotation=dict(type="dict", options=rotation_spec),
                            upload_file=dict(type="str"),
                            upload_url=dict(type="str"),
                            debug=dict(type="bool", default=False))

        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_together=[['upload_file', 'upload_url']])

    def validate_rotation(self, rotation):
        size_pct = rotation.get('size_pct', None)
        max_num = rotation.get('max_num', None)
        if size_pct and (float(size_pct) < 0 or float(size_pct) > 100):
            self._module.fail_json(
                msg='logging size_pct must be in range 0-100')
        elif max_num and (int(max_num) < 0 or int(max_num) > self.MAX_FILES):
            self._module.fail_json(
                msg='logging max_num must positive number less than {0}'.format(self.MAX_FILES))

    def validate_upload_url(self, upload_url):
        check = self.URL_REGEX.match(upload_url)
        if upload_url and not check:
            self._module.fail_json(
                msg='Invalid url, make sure that you use "[ftp, scp, tftp, sftp]://username:password@hostname:/location" format')

    def validate_rotation_max_num(self, max_num):
        if max_num and (max_num < 1 or max_num > self.MAX_FILES):
            self._module.fail_json(
                msg='logging max_num must be between 1 and 999999')

    def show_logging(self):
        show_logging = show_cmd(self._module, "show logging", json_fmt=True, fail_on_error=False)
        running_config = show_cmd(self._module, "show running-config | include .*logging.*debug-files.*", json_fmt=True, fail_on_error=False)

        if len(show_logging) > 0:
            show_logging[0]['debug'] = running_config['Lines'] if 'Lines' in running_config else []
        else:
            show_logging = [{
                'debug': running_config['Lines'] if 'Lines' in running_config else []
            }]
        return show_logging

    def load_current_config(self):
        self._current_config = dict()
        current_config = self.show_logging()[0]
        if 'Log rotation frequency' in current_config:
            freq = current_config.get('Log rotation frequency')  # daily (Once per day at midnight)
            freq_str = freq.split()[0]
            self._current_config['frequency'] = freq_str

        if 'Log rotation size threshold' in current_config:  # 19.07 megabytes or 10.000% of partition (987.84 megabytes)
            size = current_config.get('Log rotation size threshold')
            size_arr = size.split(' ')
            if '%' in size:
                size_pct_value = size_arr[0].replace('%', '')
                self._current_config['size_pct'] = float(size_pct_value)
                size_value = re.sub(r'(\(|\)|megabytes)', '', size_arr[-2]).strip()
                self._current_config['size'] = float(size_value)
            else:
                size_value = size_arr[0]
                self._current_config['size'] = float(size_value)

        if 'Number of archived log files to keep' in current_config:
            max_num = current_config.get('Number of archived log files to keep')
            self._current_config['max_num'] = int(max_num)

        '''debug params'''
        for line in current_config['debug']:
            if 'size' in line:
                self._current_config['debug_size'] = float(line.split(' ')[-1])
            if 'frequency' in line:
                self._current_config['debug_frequency'] = line.split(' ')[-1]
            if 'size-pct' in line:
                self._current_config['debug_size_pct'] = float(line.split(' ')[-1])
            if 'max-num' in line:
                self._current_config['debug_max_num'] = int(line.split(' ')[-1])

    def get_required_config(self):
        self._required_config = dict()
        required_config = dict()
        module_params = self._module.params

        if module_params.get('delete_group', None):
            required_config['delete_group'] = module_params['delete_group']
        if module_params.get('upload_file', None):
            required_config.update({'upload_file': module_params['upload_file'],
                                    'upload_url': module_params['upload_url']})
        if module_params.get('rotation', None):
            required_config['rotation'] = module_params['rotation']
        required_config['debug'] = module_params['debug']

        self.validate_param_values(required_config)
        self._required_config = required_config

    def generate_commands(self):
        required_config = self._required_config
        current_config = self._current_config

        logging_files_type = 'debug-files' if required_config['debug'] else 'files'
        debug_prefix = 'debug_' if required_config['debug'] else ''
        if required_config.get('rotation', None):
            rotation = required_config['rotation']
            for key in rotation:
                if rotation.get(key) and current_config.get(debug_prefix + key, None) != rotation.get(key):
                    cmd = self.ROTATION_CMDS[key].format(logging_files_type, rotation[key]) if key != 'force' else\
                        self.ROTATION_CMDS[key].format(logging_files_type)
                    self._commands.append(cmd)

        if required_config.get('delete_group', None):
            self._commands.append('logging {0} delete {1}'.format(logging_files_type,
                                                                  required_config['delete_group']))

        if required_config.get('upload_file', None):
            self._commands.append('logging {0} upload {1} {2}'.format(logging_files_type,
                                                                      required_config['upload_file'], required_config['upload_url']))


def main():
    """ main entry point for module execution
    """
    OnyxSyslogFilesModule.main()


if __name__ == '__main__':
    main()
