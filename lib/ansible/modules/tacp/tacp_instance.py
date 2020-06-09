#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils
from ansible.module_utils.tacp_ansible.tacp_exceptions import ActionTimedOutException, InvalidActionUuidException
from ansible.module_utils.tacp_ansible.tacp_constants import State, Action


import json
import tacp
import sys
from uuid import uuid4
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


STATE_ACTIONS = [Action.STARTED, Action.SHUTDOWN, Action.STOPPED,
                 Action.RESTARTED, Action.FORCE_RESTARTED, Action.PAUSED,
                 Action.ABSENT]


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        api_key=dict(type='str', required=True),
        name=dict(type='str', required=True),
        state=dict(type='str', required=True,
                   choices=STATE_ACTIONS),
        datacenter=dict(type='str', required=False),
        migration_zone=dict(type='str', required=False),
        storage_pool=dict(type='str', required=False),
        template=dict(type='str', required=False),
        vcpu_cores=dict(type='int', required=False),
        memory=dict(type='str', required=False),
        disks=dict(type='list', required=False),
        nics=dict(type='list', required=False),
        vtx_enabled=dict(type='bool', default=True, required=False),
        auto_recovery_enabled=dict(type='bool', default=True, required=False),
        description=dict(type='str', required=False),
        vm_mode=dict(type='str', default='Enhanced', choices=['enhanced', 'Enhanced',
                                                              'compatibility', 'Compatibility']),
        application_group={
            'type': 'str',
            'required': False,
        },

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

    def fail_with_reason(reason):
        result['msg'] = reason
        module.fail_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    def generate_instance_params(module):
        # VM does not exist yet, so we must create it
        instance_params = {}
        instance_params['instance_name'] = module.params['name']

        components = ['storage_pool', 'datacenter', 'migration_zone']
        for component in components:
            component_uuid = tacp_utils.get_component_fields_by_name(
                module.params[component], component, api_client)
            if not component_uuid:
                reason = "%s %s does not exist, cannot continue." % component.capitalize(
                ) % module.params[component]
                fail_with_reason(reason)
            instance_params['{}_uuid'.format(component)] = component_uuid

        # Check if template exists, it must in order to continue
        template_uuid = tacp_utils.get_component_fields_by_name(
            module.params['template'], 'template', api_client)
        if template_uuid:
            instance_params['template_uuid'] = template_uuid
            boot_order = tacp_utils.get_component_fields_by_name(
                module.params['template'], 'template', api_client, fields=['name', 'uuid', 'bootOrder'])
        else:
            # Template does not exist - must fail the task
            reason = "Template %s does not exist, cannot continue." % module.params[
                'template']
            fail_with_reason(reason)

        network_payloads = []
        vnic_payloads = []
        for i, nic in enumerate(module.params['nics']):
            network_uuid = tacp_utils.get_component_fields_by_name(
                nic['network'], nic['type'].lower(), api_client)

            mac_address = nic.get('mac_address')
            automatic_mac_address = not bool(mac_address)
            if 'firewall_override' in nic:
                firewall_override_uuid = tacp_utils.get_component_fields_by_name(
                    nic['firewall_override'], 'firewall_override', api_client)
            else:
                firewall_override_uuid = None

            if i == 0:
                for boot_order_item in boot_order:
                    if boot_order_item.vnic_uuid:
                        vnic_uuid = boot_order_item.vnic_uuid
                        vnic_name = boot_order_item.name

            else:
                vnic_uuid = str(uuid4())
                vnic_boot_order = len(boot_order) + i

                vnic_payload = tacp.ApiAddVnicPayload(
                    automatic_mac_address=automatic_mac_address,
                    name=vnic_name,
                    firewall_override_uuid=firewall_override_uuid,
                    network_uuid=network_uuid,
                    boot_order=vnic_boot_order,
                    mac_address=mac_address
                )
                vnic_payloads.append(vnic_payload)

            network_payload = tacp.ApiCreateOrEditApplicationNetworkOptionsPayload(
                name=vnic_name,
                automatic_mac_assignment=automatic_mac_address,
                firewall_override_uuid=firewall_override_uuid,
                network_uuid=network_uuid,
                vnic_uuid=vnic_uuid,
                mac_address=mac_address
            )
            network_payloads.append(network_payload)

        instance_params['boot_order'] = boot_order
        instance_params['networks'] = network_payloads
        instance_params['vnics'] = vnic_payloads
        instance_params['vcpus'] = module.params['vcpu_cores']
        instance_params['memory'] = tacp_utils.convert_memory_abbreviation_to_bytes(
            module.params['memory'])
        instance_params['vm_mode'] = module.params['vm_mode'].capitalize()
        instance_params['vtx_enabled'] = module.params['vtx_enabled']
        instance_params['auto_recovery_enabled'] = module.params['auto_recovery_enabled']
        instance_params['description'] = module.params['description']

        if module.params['application_group']:
            ag_resource = tacp_utils.ApplicationGroupResource(api_client)
            uuid = ag_resource.get_uuid_by_name(
                module.params['application_group']
            )
            if uuid is None:
                resp = ag_resource.create(module.params['application_group'],
                                          instance_params['datacenter_uuid'])
                uuid = resp.object_uuid

            instance_params['application_group_uuid'] = uuid

        return instance_params

    def create_instance(instance_params, api_client):
        application_resource = tacp_utils.ApplicationResource(api_client)

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
            hardware_assisted_virtualization_enabled=instance_params['vtx_enabled'],
            enable_automatic_recovery=instance_params['auto_recovery_enabled'],
            description=instance_params['description'],
            application_group_uuid=instance_params.get('application_group_uuid')
        )

        if module._verbosity >= 3:
            result['api_request_body'] = str(body)

        response = application_resource.create(body)

        result['ansible_module_results'] = application_resource.get_by_uuid(
            response.object_uuid
        ).to_dict()
        result['changed'] = True

    def instance_power_action(name, api_client, action):
        assert action in STATE_ACTIONS + [Action.RESUMED]

        application_resource = tacp_utils.ApplicationResource(api_client)

        instance_uuid = application_resource.get_uuid_by_name(name)

        application_resource.power_action_on_instance_by_uuid(
            instance_uuid, action
        )

        result['changed'] = True

    # Current state is first dimension
    # Specified state is second dimension
    power_state_dict = {
        (State.RUNNING, Action.STARTED): [],
        (State.RUNNING, Action.SHUTDOWN): [Action.SHUTDOWN],
        (State.RUNNING, Action.STOPPED): [Action.STOPPED],
        (State.RUNNING, Action.RESTARTED): [Action.RESTARTED],
        (State.RUNNING, Action.FORCE_RESTARTED): [Action.FORCE_RESTARTED],
        (State.RUNNING, Action.PAUSED): [Action.PAUSED],
        (State.RUNNING, Action.ABSENT): [Action.ABSENT],
        (State.SHUTDOWN, Action.STARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.SHUTDOWN): [],
        (State.SHUTDOWN, Action.STOPPED): [],
        (State.SHUTDOWN, Action.RESTARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.FORCE_RESTARTED): [Action.STARTED],
        (State.SHUTDOWN, Action.PAUSED): [Action.STARTED, Action.PAUSED],
        (State.SHUTDOWN, Action.ABSENT): [Action.ABSENT],
        (State.PAUSED, Action.STARTED): [Action.RESUMED],
        (State.PAUSED, Action.SHUTDOWN): [Action.RESUMED, Action.SHUTDOWN],
        (State.PAUSED, Action.STOPPED): [Action.STOPPED],
        (State.PAUSED, Action.RESTARTED): [Action.RESUMED, Action.RESTARTED],
        (State.PAUSED, Action.FORCE_RESTARTED): [Action.RESUMED, Action.FORCE_RESTARTED],
        (State.PAUSED, Action.PAUSED): [],
        (State.PAUSED, Action.ABSENT): [Action.ABSENT]
    }

    # Return the inputs for debugging purposes
    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    application_resource = tacp_utils.ApplicationResource(api_client)
    instance_uuid = application_resource.get_uuid_by_name(
        module.params['name'])

    desired_state = module.params['state']

    if instance_uuid:
        instance_properties = application_resource.get_by_uuid(
<<<<<<< HEAD
            instance_uuid)
        current_state = instance_properties.to_dict()['status']
=======
            instance_uuid).to_dict()
        current_state = instance_properties['status']
>>>>>>> 1c1a4440f8... Update tacp_instance.py
    else:
        if module.params['state'] == 'absent':
            instance_power_action(
                module.params['name'], api_client, Action.ABSENT)
        else:
            # Application does not exist yet, so create it
            instance_params = generate_instance_params(module)
            create_instance(instance_params, api_client)
            current_state = State.SHUTDOWN

    if current_state in [State.RUNNING, State.SHUTDOWN, State.PAUSED]:
        for power_action in power_state_dict[(current_state, desired_state)]:
            instance_power_action(
                module.params['name'], api_client, power_action)

    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
