#!/usr/bin/python
# (c) 2016, NetApp, Inc
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
#

#!/usr/bin/python

DOCUMENTATION = '''

module: sf_volume_pair_manager

short_description: Manage Volume pairing

description:
- Create, delete, or update Volume pairs
    - auth_basic

options:

    hostname:
        required: true
        description:
        - hostname

    username:
        required: true
        description:
        - username

    password:
        required: true
        description:
        - password

    action:
        required: true
        description:
        - Create, Update, or Delete volume pairing
        choices: ['create', 'delete', 'update']

    first_volume_id:
        required: true when action == create or when action == delete
        -  The ID of the volume on which to start the pairing process.

    second_volume_id:
        required: true when action == create or when action == delete
        -  The ID of volume on which to complete the pairing process.

    pause:
        required: false
        description:
        - Pause / Resume volume replication
        choices: ['true', 'false']

    mode:
        required: false
        description:
        - The mode of the volume on which to start the pairing process.
        - The mode can only be set if the volume is the source volume.
        choices: ['Async', 'Sync', 'SnapshotsOnly']

            Async:
                    (default if no mode parameter specified) Writes are acknowledged when they complete locally.
                    The cluster does not wait for writes to be replicated to the target cluster.

            Sync:
                    Source acknowledges write when the data is stored locally and on the remote cluster.

            SnapshotsOnly:
                    Only snapshots created on the source cluster will be replicated.
                    Active writes from the source volume will not be replicated.

'''

import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory


class SolidFireClusterPairing(object):

    def __init__(self):

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'update']),

                first_volume_id=dict(type='int', default=None),
                second_volume_id=dict(type='int', default=None),
                pause=dict(required=False, type='bool', default=None),
                mode=dict(required=False, choices=['Async', 'Sync', 'SnapshotsOnly']),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['first_volume_id', 'second_volume_id']),
                ('action', 'delete', ['first_volume_id', 'second_volume_id']),
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        self.first_volume_id = p['first_volume_id']
        self.second_volume_id = p['second_volume_id']
        self.pause = p['pause']
        self.mode = p['mode']

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def start_volume_pairing(self):
        logger.debug('Start volume pairing')

        try:
            self.sfe.start_volume_pairing(volume_id=self.first_volume_id, mode=self.mode)

        except Exception as e:
            logger.exception('Error starting volume pairing : %s', e)

    def complete_volume_pair(self, pairing_key):
        logger.debug('Completing volume pair')

        try:
            result = self.sfe.complete_volume_pairing(volume_pairing_key=pairing_key, volume_id=self.second_volume_id)
            return result

        except Exception as e:
            logger.exception('Error completing volume pair : %s', e)
            raise

    def delete_volume_pair(self):
        logger.debug('Deleting volume pair between %s and %s ', self.first_volume_id, self.second_volume_id)

        try:
            self.sfe.remove_volume_pair(volume_id=self.first_volume_id)
            self.sfe.remove_volume_pair(volume_id=self.second_volume_id)
        except Exception as e:
            logger.exception('Error removing volume pair between %s and %s: %s', self.first_volume_id,
                             self.second_volume_id, e)
            raise

    def update_volume_pair(self):
        logger.debug('Updating volume pair for %s', self.first_volume_id)

        try:
            self.sfe.modify_volume_pair(volume_id=self.first_volume_id, paused_manual=self.pause, mode=self.mode)

        except Exception as e:
            logger.exception('Error updating volume pair for %s: %s', self.first_volume_id, e)
            raise

    def apply(self):
        changed = False

        if self.action == 'create':
            self.start_volume_pairing()
            changed = True

        elif self.action == 'delete':
            self.delete_volume_pair()
            changed = True

        elif self.action == 'update':
            self.update_volume_pair()
            changed = False

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireClusterPairing()

    try:
        v.apply()
    except Exception as e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
