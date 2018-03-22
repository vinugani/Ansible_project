#!/usr/bin/env python2.7

"""
(c) 2018, Milan Ilic <milani@nordeus.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a clone of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: one_image
short_description: Manages OpenNebula images
description:
  - Manages OpenNebula images
version_added: "2.6"
requirements: 
  - python-oca
options:
  api_url:
    description:
      - URL of the OpenNebula RPC server. 
      - It is recommended to use HTTPS so that the username/password are not
      - transferred over the network unencrypted.
      - If not set then the value of the C(ONE_URL) environment variable is used.
    required: no
  api_username:
    description:
      - Name of the user to login into the OpenNebula RPC server. If not set
      - then the value of the C(ONE_USERNAME) environment variable is used.
    required: no
  api_password:
    description:
      - Password of the user to login into OpenNebula RPC server. If not set
      - then the value of the C(ONE_PASSWORD) environment variable is used.
    required: no
  id:
    description:
      - A C(id) of the image you would like to manage.
    required: no
  name:
    description:
      - A C(name) of the image you would like to manage.
    required: no
  state:
    description:
      - C(present) - state that is used to manage the image
      - C(absent) - delete the image
    required: no
    choices: ["present", "absent"]
    default: present
  enabled:
    description:
      - Whether the image should be enabled or disabled.
    required: no
    type: bool
  action:
    description:
      - Action that will be performed on the image
    required: no
    choices: ["clone", "rename", "list"]
  new_name:
    description:
      - A name that will be assigned to the existing or new image. 
      - In the case of cloning, by default C(new_name) will take the name of the origin image with the prefix 'Copy of'.
  regexp:
    description:
      - The regex pattern that restricts the list of images to be returned whose names match specified C(regexp).
      - This parameter can only be used with action C(list) to get a list of images which will be returned in the key called C(matched_images).
      - See examples for more details.
author:
    - "Milan Ilic (@ilicmilan)"
'''

EXAMPLES = '''
# Fetch the IMAGE by id
- one_image:
    id: 45
  register: result

# Print the IMAGE properties
- debug:
    msg: result

# Rename existing IMAGE
- one_image:
    name: foo-image
    action: rename
    new_name: bar-image

# Disable the IMAGE by id
- one_image:
    id: 37
    enabled: no

# Enable the IMAGE by name
- one_image:
    name: bar-image
    enabled: yes

# Clone the IMAGE by name
- one_image:
    name: bar-image
    action: clone
    new_name: bar-image-clone
  register: result
    
# Delete the IMAGE by id
- one_image:
    id: '{{ result.id }}'
    state: absent

# Fetch all IMAGEs whose name matches regex 'app-image-.*'
- one_image:
    action: list
    regexp: 'app-image-.*'
  register: app_images
'''

RETURN = '''
id:
    description: image id
    type: integer
    sample: 153
name:
    description: image name
    type: string
    sample: app1
group_id:
    description: image's group id
    type: integer
    sample: 1
group_name:
    description: image's group name
    type: string
    sample: one-users
owner_id:
    description: image's owner id
    type: integer
    sample: 143
owner_name:
    description: image's owner name
    type: string
    sample: ansible-test
state:
    description: state of image instance
    type: string
    sample: READY
used:
    description: is image in use 
    type: bool
    sample: true
running_vms:
    description: count of running vms that use this image 
    type: integer
    sample: 7
matched_images:
    description: A list of images info based on a name C(regexp) 
    type: complex
    contains:
        id:
            description: image id
            type: integer
            sample: 153
        name:
            description: image name
            type: string
            sample: app1
        group_id:
            description: image's group id
            type: integer
            sample: 1
        group_name:
            description: image's group name
            type: string
            sample: one-users
        owner_id:
            description: image's owner id
            type: integer
            sample: 143
        owner_name:
            description: image's owner name
            type: string
            sample: ansible-test
        state:
            description: state of image instance
            type: string
            sample: READY
        used:
            description: is image in use 
            type: bool
            sample: true
        running_vms:
            description: count of running vms that use this image 
            type: integer
            sample: 7
'''

try:
    import oca
    HAS_OCA=True
except ImportError:
    HAS_OCA=False

from ansible.module_utils.basic import AnsibleModule
import os

def get_image(module, client, predicate):
    pool = oca.ImagePool(client)
    # Filter -2 means fetch all images user can Use
    pool.info(filter=-2)

    for image in pool:
        if predicate(image):
            return image

    return None

def get_image_by_name(module, client, image_name):
    return get_image(module, client, lambda image: (image.name == image_name))

def get_image_by_id(module, client, image_id):
    return get_image(module, client, lambda image: (image.id == image_id))

def get_image_instance(module, client, requested_id, requested_name):
    if requested_id:
        return get_image_by_id(module, client, requested_id)
    else:
        return get_image_by_name(module, client, requested_name)

IMAGE_STATES = [ 'INIT', 'READY', 'USED', 'DISABLED', 'LOCKED', 'ERROR', 'CLONE', 'DELETE', 'USED_PERS', 'LOCKED_USED', 'LOCKED_USED_PERS' ]

def get_image_info(client, image):
    image.info()
 
    info = {
            'id': image.id,
            'name': image.name,
            'state': IMAGE_STATES[image.state],
            'running_vms': image.running_vms,
            'used': bool(image.running_vms),
            'user_name': image.uname,
            'user_id': image.uid,
            'group_name': image.gname,
            'group_id': image.gid,
            }
    
    return info

def wait_for_state(module, image, wait_timeout, state_predicate):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        image.info()
        state = image.state

        if state_predicate(state):
            return image

        time.sleep(1)

    module.fail_json(msg="Wait timeout has expired!")

def wait_for_ready(module, image, wait_timeout = 60):
    return wait_for_state(module, image, wait_timeout, lambda state: (state in [IMAGE_STATES.index('READY')]))

def wait_for_delete(module, image, wait_timeout = 60):
    return wait_for_state(module, image, wait_timeout, lambda state: (state in [IMAGE_STATES.index('DELETE')]))

def enable_image(module, client, image, enable):
    image.info()
    changed = False

    state = image.state

    if state not in [ IMAGE_STATES.index('READY'), IMAGE_STATES.index('DISABLED'), IMAGE_STATES.index('ERROR') ]:
        if enable:
            module.fail_json(msg="Cannot enable " + IMAGE_STATES[state] + " image!")
        else:
            module.fail_json(msg="Cannot disable " + IMAGE_STATES[state] + " image!")
    
    if ((enable and state != IMAGE_STATES.index('READY')) or 
        ( not enable and state != IMAGE_STATES.index('DISABLED'))):
        changed = True
    
    if changed and not module.check_mode:
        client.call('image.enable', image.id, enable)

    result = get_image_info(client, image)
    result['matched_images'] = []
    result['changed'] = changed

    return result

def clone_image(module, client, image, new_name):
    if not module.check_mode:
        if new_name is None:
            new_name = "Copy of " + image.name
    
        tmp_image = get_image_by_name(module, client, new_name)
        if tmp_image:
            module.fail_json(msg="Name '" + new_name + "' is already taken by IMAGE with id=" + str(tmp_image.id))
    
        if image.state == IMAGE_STATES.index('DISABLED'):
            module.fail_json(msg="Cannot clone DISABLED image") 
    
        new_id = client.call('image.clone', image.id, new_name)
        image = get_image_by_id(module, client, new_id)
        wait_for_ready(module, image)

    result = get_image_info(client, image)
    result['matched_images'] = []
    result['changed'] = True

    return result

def rename_image(module, client, image, new_name):
    if new_name is None:
        module.fail_json(msg="'new_name' option has to be specified when the action is 'rename'")

    if new_name == image.name:
        result = get_image_info(client, image)
        result['matched_images'] = []
        result['changed'] = False
        return result

    tmp_image = get_image_by_name(module, client, new_name)
    if tmp_image:
        module.fail_json(msg="Name '" + new_name + "' is already taken by IMAGE with id=" + str(tmp_image.id))

    if not module.check_mode:
        client.call('image.rename', image.id, new_name)
    
    result = get_image_info(client, image)
    result['matched_images'] = []
    result['changed'] = True
    return result

def fetch_images(module, client, name_pattern):
    pool = oca.ImagePool(client)
    # Filter -2 means fetch all images user can Use
    pool.info(filter=-2)
    
    images = []
    import re
    pattern = re.compile(name_pattern)

    for image in pool:
        if pattern.match(image.name):
            images.append(get_image_info(client, image))

    result['matched_images'] = images
    return result

def delete_image(module, client, image):

    if not image:
        return { 'changed': False }

    if image.running_vms > 0:
        module.fail_json(msg="Cannot delete image. There are " + str(image.running_vms) + " VMs using it.")
       
    if not module.check_mode:
        client.call('image.delete', image.id)
        wait_for_delete(module, image)

    return { 'changed': True }
    
def get_connection_info(module):

    url = module.params.get('api_url')
    username = module.params.get('api_username')
    password = module.params.get('api_password')

    if not url:
        url = os.environ.get('ONE_URL')

    if not username:
        username = os.environ.get('ONE_USERNAME')

    if not password:
        password = os.environ.get('ONE_PASSWORD')

    if not( url and username and password ):
        module.fail_json(msg="One or more connection parameters (api_url, api_username, api_password) were not specified")
    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'username', 'password'))

    return auth_params(url=url, username=username, password=password)

if __name__ == "__main__":
    fields = {
            "api_url": {"required": False, "type": "str"},
            "api_username": {"required": False, "type": "str"},
            "api_password": {"required": False, "type": "str", "no_log": True},
            "id": {"required": False, "type": "int"},
            "name": {"required": False, "type": "str"},
            "state": {
                "default": "present",
                "choices": ['present', 'absent'],
                "type": "str"
                },
            "action": {
                "choices": ['clone', 'rename', 'list'],
                "type": "str"
                },
            "enabled": {"required": False, "type": "bool"},
            "new_name": {"required": False, "type": "str"},
            "regexp": {"required": False, "type": "str"}
            }

    module = AnsibleModule(argument_spec=fields, 
            mutually_exclusive=[
                ['id','name','regexp'],
                ['regexp', 'state'], ['regexp', 'enabled'], ['regexp', 'new_name']
                ],
            required_if=[["action", "list", ["regexp"]]],
            required_one_of=[['id','name','regexp']],
            supports_check_mode=True)

    actions = {
       'clone': clone_image,
       'rename': rename_image
    }

    if not HAS_OCA:
        module.fail_json(msg='This module requires python-oca to work!')

    auth = get_connection_info(module)
    params = module.params
    id = params.get('id')
    name = params.get('name')
    state = params.get('state')
    enabled = params.get('enabled')
    rename = params.get('rename')
    action = params.get('action')
    new_name = params.get('new_name')
    regexp = params.get('regexp')
    client = oca.Client(auth.username + ':' + auth.password, auth.url)

    result = {}

    if regexp and action != 'list':
        module.fail_json(msg="Parameter 'action' has to be 'list' when the option 'regexp' is specified.")
    
    if action and action == 'list':
        result = fetch_images(module, client, regexp)
        module.exit_json(**result)

    image = get_image_instance(module, client, id, name)
    if not image and state != 'absent':
        if id:
            module.fail_json(msg="There is no image with id=" + str(id)) 
        else:
            module.fail_json(msg="There is no image with name=" + name) 
 
    if state == 'absent':
        result = delete_image(module, client, image)
    else:
        result = get_image_info(client, image)
        result['matched_images'] = []
        changed = False
 
        if enabled != None:
            result = enable_image(module, client, image, enabled)
            changed = changed or result['changed']
        if action:
            result = actions[action](module, client, image, new_name)
            changed = changed or result['changed']

        result['changed'] = changed

    module.exit_json(**result)
