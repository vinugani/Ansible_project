#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_compute_subnetwork_facts
description:
- Gather facts for GCP Subnetwork
short_description: Gather facts for GCP Subnetwork
version_added: 2.7
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  filters:
    description:
    - A list of filter value pairs. Available filters are listed here U(https://cloud.google.com/sdk/gcloud/reference/topic/filters).
    - Each additional filter in the list will act be added as an AND condition (filter1
      and filter2) .
  region:
    description:
    - URL of the GCP region for this subnetwork.
    required: true
    type: str
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: " a subnetwork facts"
  gcp_compute_subnetwork_facts:
    region: us-west1
    filters:
    - name = test_object
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
'''

RETURN = '''
resources:
  description: List of resources
  returned: always
  type: complex
  contains:
    creationTimestamp:
      description:
      - Creation timestamp in RFC3339 text format.
      returned: success
      type: str
    description:
      description:
      - An optional description of this resource. Provide this property when you create
        the resource. This field can be set only at resource creation time.
      returned: success
      type: str
    gatewayAddress:
      description:
      - The gateway address for default routes to reach destination addresses outside
        this subnetwork.
      returned: success
      type: str
    id:
      description:
      - The unique identifier for the resource.
      returned: success
      type: int
    ipCidrRange:
      description:
      - The range of internal addresses that are owned by this subnetwork.
      - Provide this property when you create the subnetwork. For example, 10.0.0.0/8
        or 192.168.0.0/16. Ranges must be unique and non-overlapping within a network.
        Only IPv4 is supported.
      returned: success
      type: str
    name:
      description:
      - The name of the resource, provided by the client when initially creating the
        resource. The name must be 1-63 characters long, and comply with RFC1035.
        Specifically, the name must be 1-63 characters long and match the regular
        expression `[a-z]([-a-z0-9]*[a-z0-9])?` which means the first character must
        be a lowercase letter, and all following characters must be a dash, lowercase
        letter, or digit, except the last character, which cannot be a dash.
      returned: success
      type: str
    network:
      description:
      - The network this subnet belongs to.
      - Only networks that are in the distributed mode can have subnetworks.
      returned: success
      type: dict
    enableFlowLogs:
      description:
      - Whether to enable flow logging for this subnetwork.
      returned: success
      type: bool
    fingerprint:
      description:
      - Fingerprint of this resource. This field is used internally during updates
        of this resource.
      returned: success
      type: str
    secondaryIpRanges:
      description:
      - An array of configurations for secondary IP ranges for VM instances contained
        in this subnetwork. The primary IP of such VM must belong to the primary ipCidrRange
        of the subnetwork. The alias IPs may belong to either primary or secondary
        ranges.
      returned: success
      type: complex
      contains:
        rangeName:
          description:
          - The name associated with this subnetwork secondary range, used when adding
            an alias IP range to a VM instance. The name must be 1-63 characters long,
            and comply with RFC1035. The name must be unique within the subnetwork.
          returned: success
          type: str
        ipCidrRange:
          description:
          - The range of IP addresses belonging to this subnetwork secondary range.
            Provide this property when you create the subnetwork.
          - Ranges must be unique and non-overlapping with all primary and secondary
            IP ranges within a network. Only IPv4 is supported.
          returned: success
          type: str
    privateIpGoogleAccess:
      description:
      - When enabled, VMs in this subnetwork without external IP addresses can access
        Google APIs and services by using Private Google Access.
      returned: success
      type: bool
    region:
      description:
      - URL of the GCP region for this subnetwork.
      returned: success
      type: str
'''

################################################################################
# Imports
################################################################################
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest
import json

################################################################################
# Main
################################################################################


def main():
    module = GcpModule(argument_spec=dict(filters=dict(type='list', elements='str'), region=dict(required=True, type='str')))

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    items = fetch_list(module, collection(module), query_options(module.params['filters']))
    if items.get('items'):
        items = items.get('items')
    else:
        items = []
    return_value = {'resources': items}
    module.exit_json(**return_value)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks".format(**module.params)


def fetch_list(module, link, query):
    auth = GcpSession(module, 'compute')
    response = auth.get(link, params={'filter': query})
    return return_if_object(module, response)


def query_options(filters):
    if not filters:
        return ''

    if len(filters) == 1:
        return filters[0]
    else:
        queries = []
        for f in filters:
            # For multiple queries, all queries should have ()
            if f[0] != '(' and f[-1] != ')':
                queries.append("(%s)" % ''.join(f))
            else:
                queries.append(f)

        return ' '.join(queries)


def return_if_object(module, response):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


if __name__ == "__main__":
    main()
