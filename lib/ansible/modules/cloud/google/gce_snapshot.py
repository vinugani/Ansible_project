#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect

DOCUMENTATION = '''
---
module: gce_snapshot
version_added: "2.3"
short_description: Create or destroy snapshots for GCE storage volumes
description:
  - Manages snapshots for GCE instances. This module manages snapshots for
    the storage volumes of a GCE compute instance.
options:
  instance_name:
    description:
      - The GCE instance to snapshot
    required: True
  snapshot_name:
    description:
      - The name of the snapshot to manage
  disks:
    description:
      - A list of disks to create snapshots for. If none is provided,
        all of the volumes will be snapshotted
    default: all
    required: False
  state:
    description:
      - Whether a snapshot should be C(present) or C(absent)
    required: false
    default: present
    choices: [present, absent]
  service_account_email:
    description:
      - GCP service account email for the project where the instance resides
    required: true
  credentials_file:
    description:
      - The path to the credentials file associated with the service account
    required: true
  project_id:
    description:
      - The GCP project ID to use
    required: true
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.19.0"
author: Rob Wagner (@robwagner33)
'''

EXAMPLES = '''
- name: Create gce snapshot
  gce_snapshot:
    instance_name: example_instance
    snapshot_name: example_snapshot
    state: present
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost

- name: Delete gce snapshot
  gce_snapshot:
    instance_name: example_instance
    snapshot_name: example_snapshot
    state: absent
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost

- name: Create snapshot of specific disk
  gce_snapshot:
    instance_name: example_instance
    snapshot_name: example_snapshot
    state: absent
    disks:
      - disk0
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost
'''

try:
    from libcloud.compute.types import Provider
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False


def find_snapshot(volume, name):
    '''
    Check if there is a snapshot already created with the given name for
    the passed in volume.

    Args:
        volume: A gce StorageVolume object to manage
        name: The name of the snapshot to look for

    Returns:
        The VolumeSnapshot object if one is found
    '''
    found_snapshot = None
    snapshots = volume.list_snapshots()
    for snapshot in snapshots:
        if name == snapshot.name:
            found_snapshot = snapshot
    return found_snapshot


def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance_name=dict(required=True),
            snapshot_name=dict(required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            disks=dict(default=None, type='list'),
            service_account_email=dict(type='str'),
            credentials_file=dict(type='path'),
            project_id=dict(type='str')
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.19.0+) is required for this module')

    gce = gce_connect(module)

    instance_name = module.params.get('instance_name')
    snapshot_name = module.params.get('snapshot_name')
    disks = module.params.get('disks')
    state = module.params.get('state')

    changed = False
    snapshot = None
    msg = ''

    instance = gce.ex_get_node(instance_name, 'all')
    for disk in instance.extra['disks']:
        if disks is None or disk['deviceName'] in disks:
            volume_obj = gce.ex_get_volume(disk['deviceName'])
            snapshot = find_snapshot(volume_obj, snapshot_name)

            if snapshot and state == 'present':
                msg = snapshot_name + " already exists"
            elif snapshot and state == 'absent':
                snapshot.destroy()
                changed = True
                msg = snapshot_name + " was deleted"
            elif not snapshot and state == 'present':
                volume_obj.snapshot(snapshot_name)
                changed = True
                msg = snapshot_name + " created"
            elif not snapshot and state == 'absent':
                msg = snapshot_name + " already absent"

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
