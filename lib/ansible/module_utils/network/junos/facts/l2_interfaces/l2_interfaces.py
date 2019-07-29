#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos l2_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.l2_interfaces.l2_interfaces import L2_interfacesArgs
from ansible.module_utils.six import string_types
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class L2_interfacesFacts(object):
    """ The junos l2_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L2_interfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param data: previously collected configuration as lxml ElementTree root instance
                     or valid xml sting
        :rtype: dictionary
        :returns: facts
        """
        if not HAS_LXML:
            self._module.fail_json(msg='lxml is not installed.')

        if not data:
            config_filter = """
                <configuration>
                    <interfaces/>
                </configuration>
                """
            data = connection.get_configuration(filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data, errors='surrogate_then_replace'))

        self._resources = data.xpath('configuration/interfaces/interface')

        objs = []
        for resource in self._resources:
            if resource is not None:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['l2_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['l2_interfaces'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """`
        Render config as dictionary structure and delete keys
          from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The ElementTree instance of configuration object
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        enhanced_layer = True
        mode = utils.get_xml_conf_arg(conf, 'unit/family/ethernet-switching/interface-mode')

        if mode is None:
            mode = utils.get_xml_conf_arg(conf, 'unit/family/ethernet-switching/port-mode')
            enhanced_layer = False

        # Layer 2 is configured on interface
        if mode:
            config['name'] = utils.get_xml_conf_arg(conf, 'name')
            unit = utils.get_xml_conf_arg(conf, 'unit/name')
            config['unit'] = unit if unit else 0
            config['enhanced_layer'] = enhanced_layer

            if mode == 'access':
                config['access'] = {}
                config['access']['vlan'] = utils.get_xml_conf_arg(conf, "unit/family/ethernet-switching/vlan/members")
            elif mode == 'trunk':
                config['trunk'] = {}
                vlan_members = conf.xpath('unit/family/ethernet-switching/vlan/members')
                if vlan_members:
                    config['trunk']['allowed_vlans'] = []
                    for vlan_member in vlan_members:
                        config['trunk']['allowed_vlans'].append(vlan_member.text)

                config['trunk']['native_vlan'] = utils.get_xml_conf_arg(conf, "native-vlan-id")

        return utils.remove_empties(config)
