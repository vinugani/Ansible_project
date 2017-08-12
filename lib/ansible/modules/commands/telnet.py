# this is a virtual module that is entirely implemented server side
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: telnet
short_description: Executes a low-down and dirty telnet command
version_added: 2.4
description:
     - Executes a low-down and dirty telnet command, not going through the module subsystem.
     - This is mostly to be used for enabling ssh on devices that only have telnet enabled by default.
options:
  commands:
    description:
      - List of commands to be executed in the telnet session.
    required: True
  host:
    description:
        - The host/target on which to execute the command
    required: False
    default: remote_addr
  user:
    description:
        - The user for login
    required: False
    default: remote_user
  password:
    description:
        - The password for login
  port:
    description:
        - Remote port to use
    default: 23
  timeout:
    description:
        - timeout for remote operations
    default: 120
  prompts:
    description:
      - List of prompts expected before sending next command
    required: False
    default: ['$']
  pause:
    description:
        - Seconds to pause between each command issued
    required: False
    default: 1
notes:
    - The C(environment) keyword does not work with this task
author:
    - Ansible Core Team
'''

EXAMPLES = '''
- name: send configuration commands to IOS
  telnet:
    user: cisco
    password: cisco
    login_prompt: "Username: "
    prompts:
      - "[>|#]"
    commands:
      - terminal length 0
      - configure terminal
      - hostname ios01

- name: run show commands
  telnet:
    user: cisco
    password: cisco
    login_prompt: "Username: "
    prompts:
      - "[>|#]"
    commands:
      - terminal length 0
'''

RETURN = '''
output:
    description: output of each command is an element in this list
    type: list
    returned: always
    sample: [ 'success', 'success', '', 'warning .. something' ]
'''
