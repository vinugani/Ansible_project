# -*- coding: utf-8 -*-
# (c) 2016, Tom Melendez <tom@supertom.com>
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
from units.compat import unittest
from ansible.module_utils.gcp_utils import GcpRequest, navigate_hash


class NavigateHashTestCase(unittest.TestCase):
    def test_one_level(self):
        value = {
            'key': 'value'
        }
        self.assertEquals(navigate_hash(value, ['key']), value['key'])

    def test_multilevel(self):
        value = {
            'key': {
                'key2': 'value'
            }
        }
        self.assertEquals(navigate_hash(value, ['key', 'key2']), value['key']['key2'])

    def test_default(self):
        value = {
            'key': 'value'
        }
        default = 'not found'
        self.assertEquals(navigate_hash(value, ['key', 'key2'], default), default)


class GCPRequestDifferenceTestCase(unittest.TestCase):
    def test_simple_no_difference(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

    def test_simple_different(self):
        value1 = {
            'foo': 'bar',
            'test': 'original'
        }
        value2 = {
            'foo': 'bar',
            'test': 'different'
        }
        difference = {
            'test': 'original'
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

    def test_nested_dictionaries_no_difference(self):
        value1 = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            },
            'test': 'original'
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

    def test_nested_dictionaries_with_difference(self):
        value1 = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            },
            'test': 'original'
        }
        value2 = {
            'foo': {
                'quiet': {
                    'tree': 'baz'
                },
                'bar': 'hello'
            },
            'test': 'original'
        }
        difference = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
                'bar': 'baz'
            }
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

    def test_arrays_strings_no_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar'
            ]
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

    def test_arrays_strings_with_difference(self):
        value1 = {
            'foo': [
                'baz',
                'bar',
            ]
        }

        value2 = {
            'foo': [
                'baz',
                'hello'
            ]
        }
        difference = {
            'foo': [
                'bar',
            ]
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)

    def test_arrays_dicts_with_no_difference(self):
        value1 = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                },
                {
                    'different': 'dict'
                }
            ]
        }
        request = GcpRequest(value1)
        self.assertEquals(request, request)

    def test_arrays_dicts_with_difference(self):
        value1 = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                },
                {
                    'different': 'dict'
                }
            ]
        }
        value2 = {
            'foo': [
                {
                    'test': 'value2',
                    'foo': 'bar2'
                },
            ]
        }
        difference = {
            'foo': [
                {
                    'test': 'value',
                    'foo': 'bar'
                }
            ]
        }
        request1 = GcpRequest(value1)
        request2 = GcpRequest(value2)
        self.assertNotEquals(request1, request2)
        self.assertEquals(request1.difference(request2), difference)
