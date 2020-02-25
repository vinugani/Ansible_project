# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

import pytest

from ansible.module_utils.common import warnings


@pytest.mark.parametrize('ansible_module_args', [{}], indirect=['ansible_module_args'])
def test_warn(ansible_module, capfd):

    ansible_module.warn('warning1')

    with pytest.raises(SystemExit):
        ansible_module.exit_json(warnings=['warning2'])
    out, err = capfd.readouterr()
    assert json.loads(out)['warnings'] == ['warning1', 'warning2']


@pytest.mark.parametrize('ansible_module_args', [{}], indirect=['ansible_module_args'])
def test_deprecate(ansible_module, capfd, monkeypatch):
    monkeypatch.setattr(warnings, '_global_deprecations', [])

    ansible_module.deprecate('deprecation1')
    ansible_module.deprecate('deprecation2', '2.3')  # pylint: disable=ansible-deprecated-no-collection-name
    ansible_module.deprecate('deprecation3', version='2.4')  # pylint: disable=ansible-deprecated-no-collection-name
    ansible_module.deprecate('deprecation4', date='2020-03-10')  # pylint: disable=ansible-deprecated-no-collection-name
    ansible_module.deprecate('deprecation5', collection_name='ansible.builtin')
    ansible_module.deprecate('deprecation6', '2.3', collection_name='ansible.builtin')
    ansible_module.deprecate('deprecation7', version='2.4', collection_name='ansible.builtin')
    ansible_module.deprecate('deprecation8', date='2020-03-10', collection_name='ansible.builtin')

    with pytest.raises(SystemExit):
        ansible_module.exit_json(deprecations=['deprecation9', ('deprecation10', '2.4')])

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'deprecation1', u'version': None, u'collection_name': None},
        {u'msg': u'deprecation2', u'version': '2.3', u'collection_name': None},
        {u'msg': u'deprecation3', u'version': '2.4', u'collection_name': None},
        {u'msg': u'deprecation4', u'date': '2020-03-10', u'collection_name': None},
        {u'msg': u'deprecation5', u'version': None, u'collection_name': 'ansible.builtin'},
        {u'msg': u'deprecation6', u'version': '2.3', u'collection_name': 'ansible.builtin'},
        {u'msg': u'deprecation7', u'version': '2.4', u'collection_name': 'ansible.builtin'},
        {u'msg': u'deprecation8', u'date': '2020-03-10', u'collection_name': 'ansible.builtin'},
        {u'msg': u'deprecation9', u'version': None, u'collection_name': None},
        {u'msg': u'deprecation10', u'version': '2.4', u'collection_name': None},
    ]


@pytest.mark.parametrize('ansible_module_args', [{}], indirect=['ansible_module_args'])
def test_deprecate_without_list(ansible_module, capfd):
    with pytest.raises(SystemExit):
        ansible_module.exit_json(deprecations='Simple deprecation warning')

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'Simple deprecation warning', u'version': None, u'collection_name': None},
    ]


@pytest.mark.parametrize('ansible_module_args', [{}], indirect=['ansible_module_args'])
def test_deprecate_without_list(ansible_module, capfd):
    with pytest.raises(AssertionError) as ctx:
        ansible_module.deprecate('Simple deprecation warning', date='', version='')
    assert ctx.value.args[0] == "implementation error -- version and date must not both be set"
