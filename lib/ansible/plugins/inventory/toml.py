# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: toml
    version_added: "2.8"
    short_description: Uses a specific TOML file as an inventory source.
    description:
        - TOML based inventory format
        - File MUST have a valid '.toml' file extension
    notes:
        - To function it requires the 'toml' plugin being whitelisted in configuration.
        - Requires the 'toml' python library
'''

EXAMPLES = '''
example1: |
    [all.vars]
    has_java = false

    [web]
    children = [
        "apache",
        "nginx"
    ]
    vars = { http_port = 8080, myvar = 23 }

    [web.hosts]
    host1 = {}
    host2 = { ansible_port = 222 }

    [apache.hosts]
    tomcat1 = {}
    tomcat2 = { myvar = 34 }
    tomcat3 = { mysecret = "03#pa33w0rd" }

    [nginx.hosts]
    jenkins1 = {}

    [nginx.vars]
    has_java = true

example2: |
    [all.vars]
    has_java = false

    [web]
    children = [
        "apache",
        "nginx"
    ]

    [web.vars]
    http_port = 8080
    myvar = 23

    [web.hosts.host1]
    [web.hosts.host2]
    ansible_port = 222

    [apache.hosts.tomcat1]

    [apache.hosts.tomcat2]
    myvar = 34

    [apache.hosts.tomcat3]
    mysecret = "03#pa33w0rd"

    [nginx.hosts.jenkins1]

    [nginx.vars]
    has_java = true

example3: |
    [ungrouped.hosts]
    host1 = {}
    host2 = { ansible_host = "127.0.0.1", ansible_port = 44 }
    host3 = { ansible_host = "127.0.0.1", ansible_port = 45 }

    [g1.hosts]
    host4 = {}

    [g2.hosts]
    host4 = {}
'''

import os

from collections import MutableMapping, MutableSequence

from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.inventory import BaseFileInventoryPlugin

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False


class InventoryModule(BaseFileInventoryPlugin):
    NAME = 'toml'

    def __init__(self):
        if not HAS_TOML:
            raise AnsibleParserError('The TOML inventory plugin requires the python "toml" library')

        super(InventoryModule, self).__init__()

    def _parse_group(self, group, group_data):
        if not isinstance(group_data, (MutableMapping, type(None))):
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)
            return

        self.inventory.add_group(group)
        if group_data is not None:
            for key, data in group_data.items():
                if key == 'vars':
                    if not isinstance(data, MutableMapping):
                        raise AnsibleParserError(
                            'Invalid "vars" entry for "%s" group, requires a dict, found "%s" instead.' %
                            (group, type(data))
                        )
                    for var, value in data.items():
                        self.inventory.set_variable(group, var, value)

                elif key == 'children':
                    if not isinstance(data, MutableSequence):
                        raise AnsibleParserError(
                            'Invalid "vars" entry for "%s" group, requires a list, found "%s" instead.' %
                            (group, type(data))
                        )
                    for subgroup in data:
                        self._parse_group(subgroup, {})
                        self.inventory.add_child(group, subgroup)

                elif key == 'hosts':
                    if not isinstance(data, MutableMapping):
                        raise AnsibleParserError(
                            'Invalid "hosts" entry for "%s" group, requires a dict, found "%s" instead.' %
                            (group, type(data))
                        )
                    for host_pattern, value in data.items():
                        hosts, port = self._expand_hostpattern(host_pattern)
                        self._populate_host_vars(hosts, value, group, port)
                else:
                    self.display.warning(
                        'Skipping unexpected key "%s" in group "%s", only "vars", "children" and "hosts" are valid' %
                        (key, group)
                    )

    def _load_file(self, file_name):
        if not file_name or not isinstance(file_name, string_types):
            raise AnsibleParserError("Invalid filename: '%s'" % to_native(file_name))

        b_file_name = to_bytes(self.loader.path_dwim(file_name))
        if not self.loader.path_exists(b_file_name):
            raise AnsibleFileNotFound("Unable to retrieve file contents", file_name=file_name)

        try:
            with open(b_file_name, 'r') as f:
                return toml.load(f)
        except toml.TomlDecodeError as e:
            raise AnsibleParserError(
                'TOML file (%s) is invalid: %s' % (file_name, to_native(e)),
                orig_exc=e
            )
        except (IOError, OSError) as e:
            raise AnsibleParserError(
                "An error occurred while trying to read the file '%s': %s" % (file_name, to_native(e)),
                orig_exc=e
            )
        except Exception as e:
            raise AnsibleParserError(
                "An unexpected error occurred while parsing the file '%s': %s" % (file_name, to_native(e)),
                orig_exc=e
            )

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''
        super(InventoryModule, self).parse(inventory, loader, path)
        self.set_options()

        try:
            data = self._load_file(path)
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            raise AnsibleParserError('Parsed empty TOML file')
        elif data.get('plugin'):
            raise AnsibleParserError('Plugin configuration TOML file, not TOML inventory')

        for group_name in data:
            self._parse_group(group_name, data[group_name])

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)
            if not ext or ext == '.toml':
                return True
        return False
