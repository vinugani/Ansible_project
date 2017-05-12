# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars, get_unique_id

__all__ = ['Host']

class Host:
    ''' a single ansible host '''

    #__slots__ = [ 'name', 'vars', 'groups' ]

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, data):
        return self.deserialize(data)

    def __eq__(self, other):
        if not isinstance(other, Host):
            return False
        return self._uuid == other._uuid

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def serialize(self):
        groups = []
        for group in self.groups:
            groups.append(group.serialize())

        return dict(
            name=self.name,
            vars=self.vars.copy(),
            address=self.address,
            uuid=self._uuid,
            gathered_facts=self._gathered_facts,
            groups=groups,
            implicit=self.implicit,
        )

    def deserialize(self, data):
        self.__init__(gen_uuid=False)

        self.name    = data.get('name')
        self.vars    = data.get('vars', dict())
        self.address = data.get('address', '')
        self._uuid   = data.get('uuid', None)
        self.implicit= data.get('implicit', False)

        groups = data.get('groups', [])
        for group_data in groups:
            g = Group()
            g.deserialize(group_data)
            self.groups.append(g)

    def __init__(self, name=None, port=None, gen_uuid=True):

        self.name = name
        self.vars = {}
        self.groups = []

        self.address = name

        if port:
            self.set_variable('ansible_port', int(port))

        self._gathered_facts = False
        self._uuid = None
        if gen_uuid:
            self._uuid = get_unique_id()
        self.implicit = False

    def __repr__(self):
        return "Host(name='{0}')".format(self.get_name())

    def get_name(self):
        return self.name

    @property
    def gathered_facts(self):
        return self._gathered_facts

    def set_gathered_facts(self, gathered):
        self._gathered_facts = gathered

    def populate_ancestors(self):

        # populate ancestors
        for group in self.groups:
            self.add_group(group)

    def add_group(self, group):

        # populate ancestors
        for oldg in group.get_ancestors():
            if oldg not in self.groups:
                self.add_group(oldg)

        if group not in self.groups:
            self.groups.append(group)

    def remove_group(self, group):

        if group in self.groups:
            self.groups.remove(group)

            # remove exclusive ancestors, xcept all!
            for oldg in group.get_ancestors():
                if oldg.name != 'all':
                    for childg in self.groups:
                        if oldg in childg.get_ancestors():
                            break
                    else:
                        self.remove_group(oldg)

    def set_variable(self, key, value):

        self.vars[key]=value

    def get_groups(self):
        return self.groups

    def get_vars(self):

        results = {}
        results = combine_vars(results, self.vars)
        results['inventory_hostname'] = self.name
        results['inventory_hostname_short'] = self.name.split('.')[0]
        results['group_names'] = sorted([ g.name for g in self.get_groups() if g.name != 'all'])
        return results

    def get_group_vars(self):
        results = {}
        groups = self.get_groups()
        for group in sorted(groups, key=lambda g: (g.depth, g.priority, g.name)):
            results = combine_vars(results, group.get_vars())
        return results
