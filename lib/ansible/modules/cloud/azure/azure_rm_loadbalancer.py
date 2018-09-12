#!/usr/bin/python
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_loadbalancer

version_added: "2.4"

short_description: Manage Azure load balancers.

description:
    - Create, update and delete Azure load balancers

options:
    resource_group:
        description:
            - Name of a resource group where the load balancer exists or will be created.
        required: true
    name:
        description:
            - Name of the load balancer.
        required: true
    state:
        description:
            - Assert the state of the load balancer. Use C(present) to create/update a load balancer, or
              C(absent) to delete one.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    sku:
        description:
            The load balancer SKU.
        choices:
            - Basic
            - Standard
        version_added: 2.6
    frontend_ip_configurations:
        description: List of frontend IPs to be used
        suboptions:
            name:
                description: Name of the frontend ip configuration.
                required: True
            public_ip_address:
                description: Name of an existing public IP address object in the current resource group to associate with the security group.
            private_ip_address:
                description: The reference of the Public IP resource.
                version_added: 2.6
            private_ip_allocation_method:
                description: The Private IP allocation method.
                choices:
                    - Static
                    - Dynamic
                version_added: 2.6
            subnet:
                description:
                    - The reference of the subnet resource.
                    - Should be an existing subnet's resource id.
                version_added: 2.6
        version_added: 2.5
    backend_address_pools:
        description: List of backend address pools
        suboptions:
            name:
                description: Name of the backend address pool.
                required: True
        version_added: 2.5
    probes:
        description: List of probe definitions used to check endpoint health.
        suboptions:
            name:
                description: Name of the probe.
                required: True
            port:
                description: Probe port for communicating the probe. Possible values range from 1 to 65535, inclusive.
                required: True
            protocol:
                description:
                    - The protocol of the end point to be probed.
                    - If 'Tcp' is specified, a received ACK is required for the probe to be successful.
                    - If 'Http' is specified, a 200 OK response from the specified URL is required for the probe to be successful.
                choices:
                    - Tcp
                    - Http
                default: Tcp
            interval:
                description:
                    - The interval, in seconds, for how frequently to probe the endpoint for health status.
                    - Slightly less than half the allocated timeout period, which allows two full probes before taking the instance out of rotation.
                    - The default value is 15, the minimum value is 5.
                default: 15
            fail_count:
                description:
                    - The number of probes where if no response, will result in stopping further traffic from being delivered to the endpoint.
                    - This values allows endpoints to be taken out of rotation faster or slower than the typical times used in Azure.
                default: 3
                aliases:
                    - number_of_probes
            request_path:
                description:
                    - The URI used for requesting health status from the VM.
                    - Path is required if a protocol is set to http. Otherwise, it is not allowed.
        version_added: 2.5
    inbound_nat_pools:
        description:
            - Defines an external port range for inbound NAT to a single backend port on NICs associated with a load balancer.
            - Inbound NAT rules are created automatically for each NIC associated with the Load Balancer using an external port from this range.
            - Defining an Inbound NAT pool on your Load Balancer is mutually exclusive with defining inbound Nat rules.
            - Inbound NAT pools are referenced from virtual machine scale sets.
            - NICs that are associated with individual virtual machines cannot reference an inbound NAT pool.
            - They have to reference individual inbound NAT rules.
        suboptions:
            name:
                description: Name of the inbound NAT pool.
                required: True
            frontend_ip_configuration_name:
                description: A reference to frontend IP addresses.
                required: True
            protocol:
                description: IP protocol for the NAT pool
                choices:
                    - Tcp
                    - Udp
                    - All
                default: Tcp
            frontend_port_range_start:
                description:
                    - The first port in the range of external ports that will be used to provide inbound NAT to NICs associated with the load balancer.
                    - Acceptable values range between 1 and 65534.
                required: True
            frontend_port_range_end:
                description:
                    - The last port in the range of external ports that will be used to provide inbound NAT to NICs associated with the load balancer.
                    - Acceptable values range between 1 and 65535.
                required: True
            backend_port:
                description:
                    - The port used for internal connections on the endpoint.
                    - Acceptable values are between 1 and 65535.
        version_added: 2.5
    load_balancing_rules:
        description:
            - Object collection representing the load balancing rules Gets the provisioning.
        suboptions:
            name:
                description: name of the load balancing rule.
                required: True
            frontend_ip_configuration:
                description: A reference to frontend IP addresses.
                required: True
            backend_address_pool:
                description: A reference to a pool of DIPs. Inbound traffic is randomly load balanced across IPs in the backend IPs.
                required: True
            probe:
                description: The name of the load balancer probe this rule should use for health checks.
                required: True
            protocol:
                description: IP protocol for the load balancing rule.
                choices:
                    - Tcp
                    - Udp
                    - All
                default: Tcp
            load_distribution:
                description:
                    - The session persistence policy for this rule; C(Default) is no persistence.
                choices:
                    - Default
                    - SourceIP
                    - SourceIPProtocol
                default: Default
            frontend_port:
                description:
                    - The port for the external endpoint.
                    - Frontend port numbers must be unique across all rules within the load balancer.
                    - Acceptable values are between 0 and 65534.
                    - Note that value 0 enables "Any Port"
            backend_port:
                description:
                    - The port used for internal connections on the endpoint.
                    - Acceptable values are between 0 and 65535.
                    - Note that value 0 enables "Any Port"
            idle_timeout:
                description:
                    - The timeout for the TCP idle connection.
                    - The value can be set between 4 and 30 minutes.
                    - The default value is 4 minutes.
                    - This element is only used when the protocol is set to TCP.
            enable_floating_ip:
                description:
                    - Configures SNAT for the VMs in the backend pool to use the publicIP address specified in the frontend of the load balancing rule.
        version_added: 2.5
    public_ip_address_name:
        description:
            - (deprecated) Name of an existing public IP address object to associate with the security group.
            - This option has been deprecated, and will be removed in 2.9. Use I(frontend_ip_configurations) instead.
        aliases:
            - public_ip_address
            - public_ip_name
            - public_ip
        required: false
    probe_port:
        description:
            - (deprecated) The port that the health probe will use.
            - This option has been deprecated, and will be removed in 2.9. Use I(probes) instead.
        required: false
    probe_protocol:
        description:
            - (deprecated) The protocol to use for the health probe.
            - This option has been deprecated, and will be removed in 2.9. Use I(probes) instead.
        required: false
        choices:
            - Tcp
            - Http
    probe_interval:
        description:
            - (deprecated) Time (in seconds) between endpoint health probes.
            - This option has been deprecated, and will be removed in 2.9. Use I(probes) instead.
        default: 15
        required: false
    probe_fail_count:
        description:
            - (deprecated) The amount of probe failures for the load balancer to make a health determination.
            - This option has been deprecated, and will be removed in 2.9. Use I(probes) instead.
        default: 3
        required: false
    probe_request_path:
        description:
            - (deprecated) The URL that an HTTP probe will use (only relevant if probe_protocol is set to Http).
            - This option has been deprecated, and will be removed in 2.9. Use I(probes) instead.
        required: false
    protocol:
        description:
            - (deprecated) The protocol (TCP or UDP) that the load balancer will use.
            - This option has been deprecated, and will be removed in 2.9. Use I(load_balancing_rules) instead.
        required: false
        choices:
            - Tcp
            - Udp
    load_distribution:
        description:
            - (deprecated) The type of load distribution that the load balancer will employ.
            - This option has been deprecated, and will be removed in 2.9. Use I(load_balancing_rules) instead.
        required: false
        choices:
            - Default
            - SourceIP
            - SourceIPProtocol
    frontend_port:
        description:
            - (deprecated) Frontend port that will be exposed for the load balancer.
            - This option has been deprecated, and will be removed in 2.9. Use I(load_balancing_rules) instead.
        required: false
    backend_port:
        description:
            - (deprecated) Backend port that will be exposed for the load balancer.
            - This option has been deprecated, and will be removed in 2.9. Use I(load_balancing_rules) instead.
        required: false
    idle_timeout:
        description:
            - (deprecated) Timeout for TCP idle connection in minutes.
            - This option has been deprecated, and will be removed in 2.9. Use I(load_balancing_rules) instead.
        default: 4
        required: false
    natpool_frontend_port_start:
        description:
            - (deprecated) Start of the port range for a NAT pool.
            - This option has been deprecated, and will be removed in 2.9. Use I(inbound_nat_pools) instead.
        required: false
    natpool_frontend_port_end:
        description:
            - (deprecated) End of the port range for a NAT pool.
            - This option has been deprecated, and will be removed in 2.9. Use I(inbound_nat_pools) instead.
        required: false
    natpool_backend_port:
        description:
            - (deprecated) Backend port used by the NAT pool.
            - This option has been deprecated, and will be removed in 2.9. Use I(inbound_nat_pools) instead.
        required: false
    natpool_protocol:
        description:
            - (deprecated) The protocol for the NAT pool.
            - This option has been deprecated, and will be removed in 2.9. Use I(inbound_nat_pools) instead.
        required: false
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Thomas Stringer (@tstringer)"
    - "Yuwei Zhou (@yuwzho)"
'''

EXAMPLES = '''
- name: create load balancer
  azure_rm_loadbalancer:
    resource_group: testrg
    name: testloadbalancer1
    frontend_ip_configurations:
      - name: frontendipconf0
        public_ip_address: testpip
    backend_address_pools:
      - name: backendaddrpool0
    probes:
      - name: prob0
        port: 80
    inbound_nat_pools:
      - name: inboundnatpool0
        frontend_ip_configuration_name: frontendipconf0
        protocol: Tcp
        frontend_port_range_start: 80
        frontend_port_range_end: 81
        backend_port: 8080
    load_balancing_rules:
      - name: lbrbalancingrule0
        frontend_ip_configuration: frontendipconf0
        backend_address_pool: backendaddrpool0
        frontend_port: 80
        backend_port: 80
        probe: prob0
'''

RETURN = '''
state:
    description: Current state of the load balancer
    returned: always
    type: dict
changed:
    description: Whether or not the resource has changed
    returned: always
    type: bool
'''

import random
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


frontend_ip_configuration_spec = dict(
    name=dict(
        type='str',
        required=True
    ),
    public_ip_address=dict(
        type='str'
    ),
    private_ip_address=dict(
        type='str'
    ),
    private_ip_allocation_method=dict(
        type='str'
    ),
    subnet=dict(
        type='str'
    )
)


backend_address_pool_spec = dict(
    name=dict(
        type='str',
        required=True
    )
)


probes_spec = dict(
    name=dict(
        type='str',
        required=True
    ),
    port=dict(
        type='int',
        required=True
    ),
    protocol=dict(
        type='str',
        choices=['Tcp', 'Http'],
        default='Tcp'
    ),
    interval=dict(
        type='int',
        default=15
    ),
    fail_count=dict(
        type='int',
        default=3,
        aliases=['number_of_probes']
    ),
    request_path=dict(
        type='str'
    )
)


inbound_nat_pool_spec = dict(
    name=dict(
        type='str',
        required=True
    ),
    frontend_ip_configuration_name=dict(
        type='str',
        required=True
    ),
    protocol=dict(
        type='str',
        choices=['Tcp', 'Udp', 'All'],
        default='Tcp'
    ),
    frontend_port_range_start=dict(
        type='int',
        required=True
    ),
    frontend_port_range_end=dict(
        type='int',
        required=True
    ),
    backend_port=dict(
        type='int',
        required=True
    )
)


load_balancing_rule_spec = dict(
    name=dict(
        type='str',
        required=True
    ),
    frontend_ip_configuration=dict(
        type='str',
        required=True
    ),
    backend_address_pool=dict(
        type='str',
        required=True
    ),
    probe=dict(
        type='str',
        required=True
    ),
    protocol=dict(
        type='str',
        choices=['Tcp', 'Udp', 'All'],
        default='Tcp'
    ),
    load_distribution=dict(
        type='str',
        choices=['Default', 'SourceIP', 'SourceIPProtocol'],
        default='Default'
    ),
    frontend_port=dict(
        type='int',
        required=True
    ),
    backend_port=dict(
        type='int'
    ),
    idle_timeout=dict(
        type='int',
        default=4
    ),
    enable_floating_ip=dict(
        type='bool'
    )
)


class AzureRMLoadBalancer(AzureRMModuleBase):
    """Configuration class for an Azure RM load balancer resource"""

    def __init__(self):
        self.module_args = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str'
            ),
            sku=dict(
                type='str',
                choices=['Basic', 'Standard']
            ),
            frontend_ip_configurations=dict(
                type='list',
                elements='dict',
                options=frontend_ip_configuration_spec
            ),
            backend_address_pools=dict(
                type='list',
                elements='dict',
                options=backend_address_pool_spec
            ),
            probes=dict(
                type='list',
                elements='dict',
                options=probes_spec
            ),
            inbound_nat_pools=dict(
                type='list',
                elements='dict',
                options=inbound_nat_pool_spec
            ),
            load_balancing_rules=dict(
                type='list',
                elements='dict',
                options=load_balancing_rule_spec
            ),
            public_ip_address_name=dict(
                type='str',
                aliases=['public_ip_address', 'public_ip_name', 'public_ip']
            ),
            probe_port=dict(
                type='int'
            ),
            probe_protocol=dict(
                type='str',
                choices=['Tcp', 'Http']
            ),
            probe_interval=dict(
                type='int',
                default=15
            ),
            probe_fail_count=dict(
                type='int',
                default=3
            ),
            probe_request_path=dict(
                type='str'
            ),
            protocol=dict(
                type='str',
                choices=['Tcp', 'Udp']
            ),
            load_distribution=dict(
                type='str',
                choices=['Default', 'SourceIP', 'SourceIPProtocol']
            ),
            frontend_port=dict(
                type='int'
            ),
            backend_port=dict(
                type='int'
            ),
            idle_timeout=dict(
                type='int',
                default=4
            ),
            natpool_frontend_port_start=dict(
                type='int'
            ),
            natpool_frontend_port_end=dict(
                type='int'
            ),
            natpool_backend_port=dict(
                type='int'
            ),
            natpool_protocol=dict(
                type='str'
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.sku = None
        self.frontend_ip_configurations = None
        self.backend_address_pools = None
        self.probes = None
        self.inbound_nat_pools = None
        self.load_balancing_rules = None
        self.public_ip_address_name = None
        self.state = None
        self.probe_port = None
        self.probe_protocol = None
        self.probe_interval = None
        self.probe_fail_count = None
        self.probe_request_path = None
        self.protocol = None
        self.load_distribution = None
        self.frontend_port = None
        self.backend_port = None
        self.idle_timeout = None
        self.natpool_frontend_port_start = None
        self.natpool_frontend_port_end = None
        self.natpool_backend_port = None
        self.natpool_protocol = None
        self.tags = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMLoadBalancer, self).__init__(
            derived_arg_spec=self.module_args,
            supports_check_mode=True
        )

    def exec_module(self, **kwargs):
        """Main module execution method"""
        for key in list(self.module_args.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        load_balancer = self.get_load_balancer()

        if self.state == 'present':
            # compatible parameters
            if not self.frontend_ip_configurations and not self.backend_address_pools and not self.probes and not self.inbound_nat_pools:
                self.deprecate('Discrete load balancer config settings are deprecated and will be removed.'
                               ' Use frontend_ip_configurations, backend_address_pools, probes, inbound_nat_pools lists instead.', version='2.9')
                frontend_ip_name = 'frontendip0'
                backend_address_pool_name = 'backendaddrp0'
                prob_name = 'prob0'
                inbound_nat_pool_name = 'inboundnatp0'
                lb_rule_name = 'lbr'
                self.frontend_ip_configurations = [dict(
                    name=frontend_ip_name,
                    public_ip_address=self.public_ip_address_name
                )]
                self.backend_address_pools = [dict(
                    name=backend_address_pool_name
                )]
                self.probes = [dict(
                    name=prob_name,
                    port=self.probe_port,
                    protocol=self.probe_protocol,
                    interval=self.probe_interval,
                    fail_count=self.probe_fail_count,
                    request_path=self.probe_request_path
                )] if self.probe_protocol else None
                self.inbound_nat_pools = [dict(
                    name=inbound_nat_pool_name,
                    frontend_ip_configuration_name=frontend_ip_name,
                    protocol=self.natpool_protocol,
                    frontend_port_range_start=self.natpool_frontend_port_start,
                    frontend_port_range_end=self.natpool_frontend_port_end,
                    backend_port=self.natpool_backend_port
                )] if self.natpool_protocol else None
                self.load_balancing_rules = [dict(
                    name=lb_rule_name,
                    frontend_ip_configuration=frontend_ip_name,
                    backend_address_pool=backend_address_pool_name,
                    probe=prob_name,
                    protocol=self.protocol,
                    load_distribution=self.load_distribution,
                    frontend_port=self.frontend_port,
                    backend_port=self.backend_port,
                    idle_timeout=self.idle_timeout,
                    enable_floating_ip=False
                )] if self.protocol else None
            if load_balancer:
                # check update, NIE
                changed = False
            else:
                changed = True
        elif self.state == 'absent' and load_balancer:
            changed = True

        self.results['state'] = load_balancer_to_dict(load_balancer)
        if 'tags' in self.results['state']:
            update_tags, self.results['state']['tags'] = self.update_tags(self.results['state']['tags'])
            if update_tags:
                changed = True
        else:
            if self.tags:
                changed = True
        self.results['changed'] = changed

        if self.state == 'present' and changed:
            # create or update
            frontend_ip_configurations_param = [self.network_models.FrontendIPConfiguration(
                name=item.get('name'),
                public_ip_address=self.get_public_ip_address_instance(item.get('public_ip_address')) if item.get('public_ip_address') else None,
                private_ip_address=item.get('private_ip_address'),
                private_ip_allocation_method=item.get('private_ip_allocation_method'),
                subnet=self.network_models.Subnet(id=item.get('subnet')) if item.get('subnet') else None
            ) for item in self.frontend_ip_configurations] if self.frontend_ip_configurations else None

            backend_address_pools_param = [self.network_models.BackendAddressPool(
                name=item.get('name')
            ) for item in self.backend_address_pools] if self.backend_address_pools else None

            probes_param = [self.network_models.Probe(
                name=item.get('name'),
                port=item.get('port'),
                protocol=item.get('protocol'),
                interval_in_seconds=item.get('interval'),
                request_path=item.get('request_path'),
                number_of_probes=item.get('fail_count')
            ) for item in self.probes] if self.probes else None

            inbound_nat_pools_param = [self.network_models.InboundNatPool(
                name=item.get('name'),
                frontend_ip_configuration=self.network_models.SubResource(
                    frontend_ip_configuration_id(
                        self.subscription_id,
                        self.resource_group,
                        self.name,
                        item.get('frontend_ip_configuration_name'))),
                protocol=item.get('protocol'),
                frontend_port_range_start=item.get('frontend_port_range_start'),
                frontend_port_range_end=item.get('frontend_port_range_end'),
                backend_port=item.get('backend_port')
            ) for item in self.inbound_nat_pools] if self.inbound_nat_pools else None

            load_balancing_rules_param = [self.network_models.LoadBalancingRule(
                name=item.get('name'),
                frontend_ip_configuration=self.network_models.SubResource(
                    frontend_ip_configuration_id(
                        self.subscription_id,
                        self.resource_group,
                        self.name,
                        item.get('frontend_ip_configuration')
                    )
                ),
                backend_address_pool=self.network_models.SubResource(
                    backend_address_pool_id(
                        self.subscription_id,
                        self.resource_group,
                        self.name,
                        item.get('backend_address_pool')
                    )
                ),
                probe=self.network_models.SubResource(
                    probe_id(
                        self.subscription_id,
                        self.resource_group,
                        self.name,
                        item.get('probe')
                    )
                ),
                protocol=item.get('protocol'),
                load_distribution=item.get('load_distribution'),
                frontend_port=item.get('frontend_port'),
                backend_port=item.get('backend_port'),
                idle_timeout_in_minutes=item.get('idle_timeout'),
                enable_floating_ip=item.get('enable_floating_ip')
            ) for item in self.load_balancing_rules] if self.load_balancing_rules else None

            param = self.network_models.LoadBalancer(
                sku=self.network_models.LoadBalancerSku(self.sku) if self.sku else None,
                location=self.location,
                tags=self.tags,
                frontend_ip_configurations=frontend_ip_configurations_param,
                backend_address_pools=backend_address_pools_param,
                probes=probes_param,
                inbound_nat_pools=inbound_nat_pools_param,
                load_balancing_rules=load_balancing_rules_param
            )

            self.results['state'] = self.create_or_update_load_balancer(param)
        elif self.state == 'absent' and changed:
            self.delete_load_balancer()
            self.results['state'] = None

        return self.results

    def get_public_ip_address_instance(self, id):
        """Get a reference to the public ip address resource"""
        self.log('Fetching public ip address {}'.format(id))
        resource_id = format_resource_id(id, self.subscription_id, 'Microsoft.Network', 'publicIPAddresses', self.resource_group)
        return self.network_models.PublicIPAddress(id=resource_id)

    def get_load_balancer(self):
        """Get a load balancer"""
        self.log('Fetching loadbalancer {0}'.format(self.name))
        try:
            return self.network_client.load_balancers.get(self.resource_group, self.name)
        except CloudError:
            return None

    def delete_load_balancer(self):
        """Delete a load balancer"""
        self.log('Deleting loadbalancer {0}'.format(self.name))
        try:
            poller = self.network_client.load_balancers.delete(self.resource_group, self.name)
            return self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error deleting loadbalancer {0} - {1}".format(self.name, str(exc)))

    def create_or_update_load_balancer(self, param):
        try:
            poller = self.network_client.load_balancers.create_or_update(self.resource_group, self.name, param)
            new_lb = self.get_poller_result(poller)
            return load_balancer_to_dict(new_lb)
        except CloudError as exc:
            self.fail("Error creating or updating load balancer {0} - {1}".format(self.name, str(exc)))


def load_balancer_to_dict(load_balancer):
    """Seralialize a LoadBalancer object to a dict"""
    if not load_balancer:
        return dict()

    result = dict(
        id=load_balancer.id,
        name=load_balancer.name,
        location=load_balancer.location,
        sku=load_balancer.sku.name,
        tags=load_balancer.tags,
        provisioning_state=load_balancer.provisioning_state,
        etag=load_balancer.etag,
        frontend_ip_configurations=[],
        backend_address_pools=[],
        load_balancing_rules=[],
        probes=[],
        inbound_nat_rules=[],
        inbound_nat_pools=[],
        outbound_nat_rules=[]
    )

    if load_balancer.frontend_ip_configurations:
        result['frontend_ip_configurations'] = [dict(
            id=_.id,
            name=_.name,
            etag=_.etag,
            provisioning_state=_.provisioning_state,
            private_ip_address=_.private_ip_address,
            private_ip_allocation_method=_.private_ip_allocation_method,
            subnet=dict(
                id=_.subnet.id,
                name=_.subnet.name,
                address_prefix=_.subnet.address_prefix
            ) if _.subnet else None,
            public_ip_address=dict(
                id=_.public_ip_address.id,
                location=_.public_ip_address.location,
                public_ip_allocation_method=_.public_ip_address.public_ip_allocation_method,
                ip_address=_.public_ip_address.ip_address
            ) if _.public_ip_address else None
        ) for _ in load_balancer.frontend_ip_configurations]

    if load_balancer.backend_address_pools:
        result['backend_address_pools'] = [dict(
            id=_.id,
            name=_.name,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.backend_address_pools]

    if load_balancer.load_balancing_rules:
        result['load_balancing_rules'] = [dict(
            id=_.id,
            name=_.name,
            protocol=_.protocol,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            backend_address_pool_id=_.backend_address_pool.id,
            probe_id=_.probe.id,
            load_distribution=_.load_distribution,
            frontend_port=_.frontend_port,
            backend_port=_.backend_port,
            idle_timeout_in_minutes=_.idle_timeout_in_minutes,
            enable_floating_ip=_.enable_floating_ip,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.load_balancing_rules]

    if load_balancer.probes:
        result['probes'] = [dict(
            id=_.id,
            name=_.name,
            protocol=_.protocol,
            port=_.port,
            interval_in_seconds=_.interval_in_seconds,
            number_of_probes=_.number_of_probes,
            request_path=_.request_path,
            provisioning_state=_.provisioning_state
        ) for _ in load_balancer.probes]

    if load_balancer.inbound_nat_rules:
        result['inbound_nat_rules'] = [dict(
            id=_.id,
            name=_.name,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            protocol=_.protocol,
            frontend_port=_.frontend_port,
            backend_port=_.backend_port,
            idle_timeout_in_minutes=_.idle_timeout_in_minutes,
            enable_floating_point_ip=_.get('enable_floating_point_ip', False),
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.inbound_nat_rules]

    if load_balancer.inbound_nat_pools:
        result['inbound_nat_pools'] = [dict(
            id=_.id,
            name=_.name,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            protocol=_.protocol,
            frontend_port_range_start=_.frontend_port_range_start,
            frontend_port_range_end=_.frontend_port_range_end,
            backend_port=_.backend_port,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.inbound_nat_pools]

    if load_balancer.outbound_nat_rules:
        result['outbound_nat_rules'] = [dict(
            id=_.id,
            name=_.name,
            allocated_outbound_ports=_.allocated_outbound_ports,
            frontend_ip_configuration_id=_.frontend_ip_configuration.id,
            backend_address_pool=_.backend_address_pool.id,
            provisioning_state=_.provisioning_state,
            etag=_.etag
        ) for _ in load_balancer.outbound_nat_rules]

    return result


def frontend_ip_configuration_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a frontend ip configuration"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/frontendIPConfigurations/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def backend_address_pool_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a backend address pool"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/backendAddressPools/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def probe_id(subscription_id, resource_group_name, load_balancer_name, name):
    """Generate the id for a probe"""
    return '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/loadBalancers/{}/probes/{}'.format(
        subscription_id,
        resource_group_name,
        load_balancer_name,
        name
    )


def main():
    """Main execution"""
    AzureRMLoadBalancer()


if __name__ == '__main__':
    main()
