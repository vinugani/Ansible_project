#!/usr/bin/python
#
# Copyright (c) 2019 Ansible, Inc
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: frr_facts
version_added: "2.8"
author: "Nilashish Chakraborty (@nilashishc)"
short_description: Collect facts from remote devices running Free Range Routing (FRR).
description:
  - Collects a base set of device facts from a remote device that
    is running FRR.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against FRR 6.0.
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         C(all), C(hardware), C(config), and C(interfaces).
      - Specify a list of values to include a larger subset.
      - Use a value with an initial C(!) to collect all facts except that subset.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- frr_facts:
    gather_subset: all

# Collect only the config and default facts
- frr_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- frr_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str

# hardware
ansible_net_mem_stats:
  description: The memory statistics fetched from the device
  returned: when hardware is configured
  type: dict

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: str

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_mpls_ldp_neighbors:
  description: The list of MPLS LDP neighbors from the remote device
  returned: when interfaces is configured and LDP daemon is running on the device
  type: dict
"""

import re

from ansible.module_utils.network.frr.frr import run_commands, get_capabilities
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(commands=cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = ['show version']

    def populate(self):
        super(Default, self).populate()
        self.facts.update(self.platform_facts())

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('version', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        return platform_facts


class Hardware(FactsBase):

    COMMANDS = ['show memory']

    def _parse_total_heap_allocated(self, data):
        match = re.search(r'Total heap allocated:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_holding_block_headers(self, data):
        match = re.search(r'Holding block headers:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_used_small_blocks(self, data):
        match = re.search(r'Used small blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_used_ordinary_blocks(self, data):
        match = re.search(r'Used ordinary blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_free_small_blocks(self, data):
        match = re.search(r'Free small blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_free_ordinary_blocks(self, data):
        match = re.search(r'Free ordinary blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_ordinary_blocks(self, data):
        match = re.search(r'Ordinary blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_small_blocks(self, data):
        match = re.search(r'Small blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_holding_blocks(self, data):
        match = re.search(r'Holding blocks:(?:\s*)(.*)', data, re.M)
        if match:
            return match.group(1)

    def _parse_daemons(self, data):
        match = re.search(r'Memory statistics for (\w+)', data, re.M)
        if match:
            return match.group(1)

    def gather_memory_facts(self, data):
        mem_details = data.split('\n\n')
        mem_stats = {}
        mem_counters = ['total_heap_allocated', 'holding_block_headers', 'used_small_blocks',
                        'used_ordinary_blocks', 'free_small_blocks', 'free_ordinary_blocks',
                        'ordinary_blocks', 'small_blocks', 'holding_blocks']

        for item in mem_details:
            daemon = self._parse_daemons(item)
            mem_stats[daemon] = {}
            for x in mem_counters:
                meth = getattr(self, '_parse_%s' % x, None)
                mem_stats[daemon][x] = meth(item)

        return mem_stats

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['mem_stats'] = self.gather_memory_facts(data)


class Config(FactsBase):

    COMMANDS = ['show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            data = re.sub(r'^Building configuration...\s+Current configuration:', '', data, flags=re.MULTILINE)
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = ['show interface']

    def populate(self):
        ldp_supported = get_capabilities(self.module)['supported_protocols']['ldp']

        if ldp_supported:
            self.COMMANDS.append('show mpls ldp discovery')

        super(Interfaces, self).populate()
        data = self.responses[0]

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()

        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)
            self.populate_ipv4_interfaces(interfaces)
            self.populate_ipv6_interfaces(interfaces)

        if ldp_supported:
            data = self.responses[1]
            if data:
                self.facts['mpls_ldp_neighbors'] = self.populate_mpls_ldp_neighbors(data)

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'^Interface (\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def populate_interfaces(self, interfaces):
        facts = dict()
        counters = ['description', 'macaddress', 'type', 'vrf', 'mtu', 'bandwidth', 'lineprotocol',
                    'operstatus']
        for key, value in iteritems(interfaces):
            intf = dict()
            for x in counters:
                meth = getattr(self, 'parse_%s' % x, None)
                intf[x] = meth(value)
            facts[key] = intf
        return facts

    def parse_description(self, data):
        match = re.search(r'Description: (.+)', data)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'HWaddr: (\S+)', data)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Type: (\S+)', data)
        if match:
            return match.group(1)

    def parse_vrf(self, data):
        match = re.search(r'vrf: (\S+)', data)
        if match:
            return match.group(1)

    def parse_mtu(self, data):
        match = re.search(r'mtu (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'bandwidth (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (\S+)', data)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = list()
            primary_address = addresses = []
            primary_address = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s{2,})', value, re.M)
            addresses = re.findall(r'inet (\S+) broadcast (?:\S+)(?:\s+)secondary', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4')
                self.facts['interfaces'][key]['ipv4'].append(ipv4)

    def populate_ipv6_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv6'] = list()
            addresses = re.findall(r'inet6 (\S+)', value, re.M)
            for address in addresses:
                addr, subnet = address.split("/")
                ipv6 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv6')
                self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def populate_mpls_ldp_neighbors(self, data):
        facts = {}
        entries = data.splitlines()
        for x in entries:
            if x.startswith('AF'):
                continue
            match = re.search(r'(\S+)(?:\s*)(\S+)(?:\s*)(\S+)(?:\s*)(\S+)(?:\s*)(\S+)', x, re.M)
            if match:
                source = match.group(4)
                neighbor = match.group(2)
                facts[source] = []
                ldp = {}
                ldp['neighbor'] = neighbor
                ldp['source'] = source
                facts[source].append(ldp)
        return facts


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
    interfaces=Interfaces
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Subset must be one of [%s], got %s' % (', '.join(VALID_SUBSETS), subset))

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
