#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_servicebus
version_added: "2.8"
short_description: Manage Azure Service Bus.
description:
    - Create, update or delete an Azure Service Bus namespaces, queues, topics, subscriptions and rules.
options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the servicebus namespace
        required: true
    state:
        description:
            - Assert the state of the route. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Namespace location.
    sku:
        description:
            - Namespace sku.
        choices:
            - standard
            - basic
            - premium
        default:
            standard

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
- name: Create a namespace
  azure_rm_servicebus:
      name: deadbeef
      location: eastus
'''
RETURN = '''
id:
    description: Current state of the service bus.
    returned: success
    type: str
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake
from ansible.module_utils._text import to_native
from datetime import datetime, timedelta


class AzureRMServiceBus(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            location=dict(type='str'),
            sku=dict(type='str', choices=['basic', 'standard', 'premium'], default='standard')
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.sku = None
        self.location = None

        self.results = dict(
            changed=False,
            id=None
        )

        super(AzureRMServiceBus, self).__init__(self.module_arg_spec,
                                                supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        changed = False

        if not self.location:
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location

        original = self.get()
        if self.state == 'present' and not original:
            self.check_name()
            changed = True
            if not self.check_mode:
                original = self.create()
        elif original:
            changed = True
            original = None
            if not self.check_mode:
                self.delete()
                self.results['deleted'] = True

        if original:
            self.results = self.to_dict()
            rules = self.get_auth_rules()
            for name in rules.keys():
                rules[name]['keys'] = self.get_sas_key(name)
            self.results['sas_policies'] = rules
        self.results['changed'] = changed
        return self.results

    def check_name(self):
        try:
            check_name = self.servicebus_client.namespaces.check_name_availability_method(self.name)
            if not check_name or not check_name.name_available:
                self.fail("Error creating namespace {0} - {1}".format(self.name, check_name.message or str(check_name)))
        except Exception as exc:
            self.fail("Error creating namespace {0} - {1}".format(self.name, check_name.message or str(check_name)))

    def create(self):
        self.log('Cannot find namespace, creating a one')
        try:
            sku = self.servicebus_models.SBSku(name=str.capitalize(self.sku))
            poller = self.servicebus_client.namespaces.create_or_update(self.resource_group,
                                                                        self.name,
                                                                        self.servicebus_models.SBNamespace(location=self.location,
                                                                                                           sku=sku))
            ns = self.get_poller_result(poller)
        except Exception as exc:
            self.fail('Error creating namespace {0} - {1}'.format(self.name, str(exc.inner_exception) or str(exc)))
        return ns

    def delete(self):
        try:
            self.servicebus_client.namespaces.delete(self.resource_group, self.name)
            return True
        except Exception as exc:
            self.fail("Error deleting route {0} - {1}".format(self.name, str(exc)))

    def get(self):
        try:
            return self.servicebus_client.namespaces.get(self.resource_group, self.name)
        except Exception:
            return None

    def to_dict(self, instance, instance_type):
        result = dict()
        attribute_map = instance_type._attribute_map
        for attribute in attribute_map.keys():
            value = getattr(instance, attribute)
            if not value:
                continue
            if isinstance(value, self.servicebus_models.SBSku):
                result[attribute] = value.name.lower()
            elif isinstance(value, datetime):
                result[attribute] = str(value)
            elif isinstance(value, str):
                result[attribute] = to_native(value)
            elif attribute == 'max_size_in_megabytes':
                result['max_size_in_mb'] = value
            else:
                result[attribute] = value
        return result

    # SAS policy
    def get_auth_rules(self):
        result = dict()
        try:
            rules = self.servicebus_client.namespaces.list_authorization_rules(self.resource_group, self.name)
            while True:
                rule = rules.next()
                result[rule.name] = self.policy_to_dict(rule)
        except Exception:
            pass
        return result

    def policy_to_dict(self, rule):
        result = rule.as_dict()
        rights = result['rights']
        if 'Manage' in rights:
            result['rights'] = 'manage'
        elif 'Listen' in rights and 'Send' in rights:
            result['rights'] = 'listen_send'
        else:
            result['rights'] = rights[0].lower()
        return result


def is_valid_timedelta(value):
    if value == timedelta(10675199, 10085, 477581):
        return None
    return value


def main():
    AzureRMServiceBus()


if __name__ == '__main__':
    main()
