#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_timezone
version_added: "2.1"
short_description: Sets Windows machine timezone
description:
  - Sets machine time to the specified timezone, the module will check if the provided timezone is supported on the machine.
notes:
  - If running on Server 2008 the hotfix https://support.microsoft.com/en-us/help/2556308/tzutil-command-line-tool-is-added-to-windows-vista-and-to-windows-server-2008
    needs to be installed to be able to run this module.
options:
  timezone:
    description:
      - Timezone to set to. Example Central Standard Time.
      - Run tzutil.exe /g to get a list of supported timezones on your server.
    required: true
author: Phil Schwartz
'''

EXAMPLES = r'''
- name: Set machine's timezone to Central Standard Time
  win_timezone:
    timezone: "Central Standard Time"
'''

RETURN = r'''# '''
