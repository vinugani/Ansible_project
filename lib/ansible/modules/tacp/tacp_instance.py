#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp import *

import json
import tacp
import sys
from tacp.rest import ApiException
from pprint import pprint

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_instance

short_description: This is my test module

version_added: "2.9"

description:
    - "This is my longer description explaining my test module"

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - tacp

author:
    - Xander Madsen (@xmadsen)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  tacp_instance:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  tacp_instance:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  tacp_instance:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
        name=dict(type='str', required=True),
        state=dict(type='str', default='present',
                   choices=['present', 'absent']),
        datacenter=dict(type='str', required=True),
        mz=dict(type='str', required=True),
        storage_pool=dict(type='str', required=True),
        template=dict(type='str', required=True),
        vcpu_cores=dict(type='int', required=True),
        memory=dict(type='str', required=True),
        disks=dict(type='list', required=True),
        nics=dict(type='list', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        args=[]
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    instance_params = {}

    # Check if VM instance with this name exists already
    instance_uuid = get_component_fields_by_name(
        module.params['name'], 'application', api_client)

    if instance_uuid:
        # VM does exist - so for now we need to just break without changing anything,
        # but in the future this would mean we go to edit the existing VM with this name/uuid
        # vm_exists = True
        result['msg'] = "An application for this datacenter already exists with name %s" % module.params['name']
        result['changed'] = False

        module.exit_json(**result)

    # VM does not exist yet, so we must create it
    instance_params['instance_name'] = module.params['name']

    # Check if storage pool exists, it must in order to continue
    storage_pool_uuid = get_component_fields_by_name(
        module.params['storage_pool'], 'storage_pool', api_client)
    if is_valid_uuid(storage_pool_uuid):
        instance_params['storage_pool_uuid'] = storage_pool_uuid
    else:
        # Pool does not exist - must fail the task
        pass

    # Check if datacenter exists, it must in order to continue
    datacenter_uuid = get_component_fields_by_name(
        module.params['datacenter'], 'datacenter', api_client)
    if is_valid_uuid(datacenter_uuid):
        instance_params['datacenter_uuid'] = datacenter_uuid
    else:
        # Datacenter does not exist - must fail the task
        pass

    # Check if migration_zone exists, it must in order to continue
    migration_zone_uuid = get_component_fields_by_name(
        module.params['mz'], 'migration_zone', api_client)
    if is_valid_uuid(migration_zone_uuid):
        instance_params['migration_zone_uuid'] = migration_zone_uuid
    else:
        # Migration zone does not exist - must fail the task
        pass

    # Check if migration_zone exists, it must in order to continue
    template_uuid = get_component_fields_by_name(
        module.params['template'], 'template', api_client)
    if is_valid_uuid(template_uuid):
        instance_params['template_uuid'] = template_uuid
        boot_order = get_component_fields_by_name(
            module.params['template'], 'template', api_client, fields=['name', 'uuid', 'bootOrder'])
    else:
        # Migration zone does not exist - must fail the task
        pass

    network_payloads = []

    for i, nic in enumerate(module.params['nics']):
        if nic['type'].lower() == "vnet":
            network_uuid = get_component_fields_by_name(
                nic['network'], 'vnet', api_client)
        elif nic['type'].lower() == "vlan":
            network_uuid = get_component_fields_by_name(
                nic['network'], 'vlan', api_client)

        if nic['mac_address']:
            automatic_mac_address = False
            mac_address = nic['mac_address']
        else:
            automatic_mac_address = True
            mac_address = None

        if i == 0:
            vnic_payloads = []
            for boot_order_item in boot_order:
                if boot_order_item.name == nic['name'] and boot_order_item.vnic_uuid:
                    vnic_uuid = boot_order_item.vnic_uuid

        else:
            # TODO - his will eventually need to be modified so that any
            # boot order is possible for any extra NICs

            vnic_uuid = str(uuid4())
            vnic_boot_order = len(boot_order) + i
            
            vnic_payload = tacp.ApiAddVnicPayload(
                automatic_mac_address=automatic_mac_address,
                name=nic['name'],
                network_uuid=network_uuid,
                boot_order=vnic_boot_order,
                mac_address=mac_address
            )
            vnic_payloads.append(vnic_payload)

        network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(
            name=nic['name'],
            automatic_mac_assignment=automatic_mac_address,
            network_uuid=network_uuid,
            vnic_uuid=vnic_uuid,
            mac_address=mac_address
        )
        network_payloads.append(network_payload)

    instance_params['boot_order'] = boot_order
    instance_params['networks'] = network_payloads
    instance_params['vnics'] = vnic_payloads
    instance_params['vcpus'] = module.params['vcpu_cores']
    instance_params['memory'] = convert_memory_abbreviation_to_bytes(
        module.params['memory'])
    instance_params['vm_mode'] = "Enhanced"

    def create_instance(instance_params):
        api_instance = tacp.ApplicationsApi(tacp.ApiClient(configuration))

        # Need to create boot disk ahead of time and provide it in the
        # ApiCreateApplicationPayload parameters

        body = tacp.ApiCreateApplicationPayload(
            name=instance_params['instance_name'],
            datacenter_uuid=instance_params['datacenter_uuid'],
            flash_pool_uuid=instance_params['storage_pool_uuid'],
            migration_zone_uuid=instance_params['migration_zone_uuid'],
            template_uuid=instance_params['template_uuid'],
            vcpus=instance_params['vcpus'],
            memory=instance_params['memory'],
            vm_mode=instance_params['vm_mode'],
            networks=instance_params['networks'],
            vnics=instance_params['vnics'],
            boot_order=instance_params['boot_order'],
            hardware_assisted_virtualization_enabled=True)
        result['api_request_body'] = str(body)
        try:
            # Create an application from a template
            api_response = api_instance.create_application_from_template_using_post(
                body)
            result['changed'] = True
            result['failed'] = False
            module.exit_json(**result)

        except ApiException as e:

            return "Exception when calling ApplicationsApi->create_application_from_template_using_post: %s\n" % e

    create_instance_response = create_instance(instance_params)

    result['create_instance_response'] = create_instance_response

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['new']:
    #     result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
