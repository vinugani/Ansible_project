#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_disk_facts
version_added: '2.5'
short_description: Show the attached disks and disk information of the target host
description:
   - With the module you can retrieve and output detailed information about the attached disks of the target.
requirements:
    - Windows 8.1 / Windows 2012R2 (NT 6.3) or newer
author:
    - Marc Tschapek (@marqelme)
notes:
  - You can use this module in combination with the win_disk_management module in order to retrieve the disks status
    on the target.
'''

EXAMPLES = r'''
- name: get disk facts
  win_disk_facts:
- name: output first disk size
  debug:
    var: ansible_facts.ansible_disk.disk_0.size

- name: get disk facts
  win_disk_facts:
- name: output second disk serial number
  debug:
    var: ansible_facts.ansible_disk.disk_1.serial_number
'''

RETURN = r'''
changed:
    description: Whether anything was changed.
    returned: always
    type: boolean
    sample: true
msg:
    description: Possible error message on failure.
    returned: failed
    type: string
    sample: "No disks could be found on the target"
ansible_facts:
    description: Dictionary containing all the detailed information about the disks of the target.
    returned: always
    type: complex
    contains:
        ansible_disk:
            description: Detailed information about found disks on the target.
            returned: always
            type: complex
            contains:
                total_disks_found:
                    description: Count of found disks on the target.
                    returned: success or failed
                    type: string
                    sample: "3"
                disk_number:
                    description: Detailed information about one particular disk.
                    returned: success or failed
                    type: complex
                    contains:
                        number:
                            description: Number of the particular disk.
                            returned: always
                            type: string
                            sample: "0"
                        size:
                            description: Size in gb of the particular disk.
                            returned: always
                            type: string
                            sample: "100gb"
                        partition_style:
                            description: Partition style of the particular disk.
                            returned: always
                            type: string
                            sample: "MBR"
                        partition_count:
                            description: Number of partitions on the particular disk.
                            returned: always
                            type: string
                            sample: "4"
                        operational_status:
                            description: Operational status of the particular disk.
                            returned: always
                            type: string
                            sample: "Online"
                        sector_size:
                            description: Sector size of the particular disk.
                            returned: always
                            type: string
                            sample: "512"
                        read_only:
                            description: Read only status of the particular disk.
                            returned: always
                            type: string
                            sample: "True"
                        boot_disk:
                            description: Information whether the particular disk is a bootable disk.
                            returned: always
                            type: string
                            sample: "False"
                        system_disk:
                            description: Information whether the particular disk is a system disk.
                            returned: always
                            type: string
                            sample: "True"
                        clustered:
                            description: Information whether the particular disk is clustered (part of a failover cluster).
                            returned: always
                            type: string
                            sample: "False"
                        model:
                            description: Model specification of the particular disk.
                            returned: always
                            type: string
                            sample: "VirtIO"
                        firmware_version:
                            description: Firmware version of the particular disk.
                            returned: always
                            type: string
                            sample: "0001"
                        location:
                            description: Location of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "PCIROOT(0)#PCI(0400)#SCSI(P00T00L00)"
                        serial_number:
                            description: Serial number of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "b62beac80c3645e5877f"
                        unique_id:
                            description: Unique ID of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "3141463431303031"
                        guid:
                            description: GUID of the particular disk on the target.
                            returned: if available
                            type: string
                            sample: "{efa5f928-57b9-47fc-ae3e-902e85fbe77f}"
'''
