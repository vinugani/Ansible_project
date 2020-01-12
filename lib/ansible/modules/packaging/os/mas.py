#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Lukas Bestle <project-ansible@lukasbestle.com>
# Copyright: (c) 2017, Michael Heap <m@michaelheap.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: mas
short_description: Manage Mac App Store applications with mas-cli
description:
    - Installs, uninstalls and updates macOS applications from the Mac App Store using the `mas-cli`.
version_added: "2.10"
author:
    - Michael Heap (@mheap)
    - Lukas Bestle (@lukasbestle)
options:
    id:
        description:
            - The Mac App Store identifier of the app(s) you want to manage.
            - This can be found by running C(mas search APP_NAME) on your machine.
        required: true
        type: list
        elements: int
    state:
        description:
            - Desired state of the app installation.
            - The C(absent) value requires root permissions, also see the examples.
        type: str
        choices:
            - absent
            - latest
            - present
        default: present
requirements:
    - macOS 10.11+
    - "`mas-cli` (U(https://github.com/mas-cli/mas)) 1.5.0+ available as C(mas) in the bin path"
    - The Apple ID to use already needs to be signed in to the Mac App Store (check with C(mas account)).
notes:
    - This module supports C(check_mode).
'''

EXAMPLES = '''
- name: Install Keynote
  mas:
    id: 409183694
    state: present

- name: Install a list of apps
  mas:
    id:
      - 409183694 # Keynote
      - 413857545 # Divvy
    state: present

- name: Ensure the latest Keynote version is installed
  mas:
    id: 409183694
    state: latest

- name: Uninstall Divvy
  mas:
    id: 413857545
    state: absent
  become: yes # Uninstallation requires root permissions
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from distutils.version import StrictVersion
import os


class Mas(object):

    def __init__(self, module):
        self.module = module

        # Initialize data properties
        self.mas_path = self.module.get_bin_path('mas')
        self._checked_signin = False
        self._installed = None # Populated only if needed
        self._outdated  = None # Populated only if needed
        self.count_install = 0
        self.count_upgrade = 0
        self.count_uninstall = 0
        self.result = {
            'changed': False
        }

        self.check_mas_tool()

    def app_command(self, command, id):
        ''' Runs a `mas` command on a given app; command can be 'install', 'upgrade' or 'uninstall' '''

        if not self.module.check_mode:
            if command != 'uninstall':
                self.check_signin()

            rc, out, err = self.run([command, str(id)])
            if rc != 0:
                self.module.fail_json(
                    msg="Error running command '{0}' on app '{1}': {2}".format(command, str(id), out.rstrip())
                )

        # No error or dry run
        self.__dict__['count_' + command] += 1

    def check_mas_tool(self):
        ''' Verifies that the `mas` tool is available in a recent version '''

        # Is the `mas` tool available at all?
        if not self.mas_path:
            self.module.fail_json(msg='Required `mas` tool is not installed')

        # Is the version recent enough?
        rc, out, err = self.run(['version'])
        if rc != 0 or not out.strip() or StrictVersion(out.strip()) < StrictVersion('1.5.0'):
            self.module.fail_json(msg='`mas` tool in version 1.5.0+ needed, got ' + out.strip())

    def check_signin(self):
        ''' Verifies that the user is signed in to the Mac App Store '''

        # Only check this once per execution
        if self._checked_signin == True:
            return

        rc, out, err = self.run(['account'])
        if out.split("\n", 1)[0].rstrip() == 'Not signed in':
            self.module.fail_json(msg='You must be signed in to the Mac App Store')

        self._checked_signin = True

    def exit(self):
        ''' Exit with the data we have collected over time '''

        msgs = []
        if self.count_install > 0:
            msgs.append('Installed {0} app(s)'.format(self.count_install))
        if self.count_upgrade > 0:
            msgs.append('Upgraded {0} app(s)'.format(self.count_upgrade))
        if self.count_uninstall > 0:
            msgs.append('Uninstalled {0} app(s)'.format(self.count_uninstall))

        if msgs:
            self.result['changed'] = True
            self.result['msg'] = ', '.join(msgs)

        self.module.exit_json(**self.result)

    def get_current_state(self, command):
        ''' Returns the list of all app IDs; command can either be 'list' or 'outdated' '''

        rc, raw_list, err = self.run([command])
        rows = raw_list.split("\n")
        list = {}
        for r in rows:
            # Format: "123456789 App Name"
            r = r.split(' ', 1)
            if len(r) == 2:
                list[r[1]] = int(r[0])

        return list

    def installed(self):
        ''' Returns the list of installed apps '''

        # Populate cache if not already done
        if self._installed == None:
            self._installed = self.get_current_state('list')

        return self._installed.values()

    def is_installed(self, id):
        ''' Checks whether the given app is installed '''

        return int(id) in self.installed()

    def is_outdated(self, id):
        ''' Checks whether the given app is installed, but outdated '''

        return int(id) in self.outdated()

    def outdated(self):
        ''' Returns the list of installed, but outdated apps '''

        # Populate cache if not already done
        if self._outdated == None:
            self._outdated = self.get_current_state('outdated')

        return self._outdated.values()

    def run(self, cmd):
        ''' Runs a command of the `mas` tool '''

        cmd.insert(0, self.mas_path)
        return self.module.run_command(cmd, False)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(type='list', elements='int', required=True),
        )
            state=dict(type='str', default='present', choices=['absent', 'latest', 'present']),
        supports_check_mode=True
    )
    mas = Mas(module)

    apps  = module.params['id']
    state = module.params['state']


    # Run operations on the given app IDs
    for app in apps:
        if state == 'present':
            if not mas.is_installed(app):
                mas.app_command('install', app)

        elif state == 'absent':
            if mas.is_installed(app):
                # Ensure we are root
                if os.getuid() != 0:
                    module.fail_json(msg="Uninstalling apps requires root permissions ('become: yes')")

                mas.app_command('uninstall', app)

        elif state == 'latest':
            if not mas.is_installed(app):
                mas.app_command('install', app)
            elif mas.is_outdated(app):
                mas.app_command('upgrade', app)

    # Exit with the collected data
    mas.exit()


if __name__ == '__main__':
    main()
