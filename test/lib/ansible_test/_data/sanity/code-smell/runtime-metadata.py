#!/usr/bin/env python
"""Schema validation of ansible-core's ansible_builtin_runtime.yml and collection's meta/runtime.yml"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import os
import re
import sys
from distutils.version import StrictVersion
from functools import partial

import yaml

from voluptuous import All, Any, MultipleInvalid, PREVENT_EXTRA
from voluptuous import Required, Schema, Invalid
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types
from ansible.utils.version import SemanticVersion


def isodate(value):
    """Validate a datetime.date or ISO 8601 date string."""
    # datetime.date objects come from YAML dates, these are ok
    if isinstance(value, datetime.date):
        return value
    # make sure we have a string
    msg = 'Expected ISO 8601 date string (YYYY-MM-DD), or YAML date'
    if not isinstance(value, string_types):
        raise Invalid(msg)
    # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
    # we have to do things manually.
    if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
        raise Invalid(msg)
    try:
        datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise Invalid(msg)
    return value


def removal_version(value, is_ansible):
    """Validate a removal version string."""
    msg = (
        'Removal version must be a string' if is_ansible else
        'Removal version must be a semantic version (https://semver.org/)'
    )
    if not isinstance(value, string_types):
        raise Invalid(msg)
    try:
        if is_ansible:
            version = StrictVersion()
            version.parse(value)
        else:
            version = SemanticVersion()
            version.parse(value)
            if version.major != 0 and (version.minor != 0 or version.patch != 0):
                raise Invalid('removal_version (%r) must be a major release, not a minor or patch release '
                              '(see specification at https://semver.org/)' % (value, ))
    except ValueError:
        raise Invalid(msg)
    return value


def any_value(value):
    """Accepts anything."""
    return value


def validate_metadata_file(path, is_ansible):
    """Validate explicit runtime metadata file"""
    try:
        with open(path, 'r') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line +
                                                  1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        return
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' %
              (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return

    # Updates to schema MUST also be reflected in the documentation
    # ~https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html

    # plugin_routing schema

    deprecation_tombstoning_schema = All(
        # The first schema validates the input, and the second makes sure no extra keys are specified
        Schema(
            {
                'removal_version': partial(removal_version, is_ansible=is_ansible),
                'removal_date': Any(isodate),
                'warning_text': Any(*string_types),
            }
        ),
        Schema(
            Any(
                {
                    Required('removal_version'): any_value,
                    'warning_text': any_value,
                },
                {
                    Required('removal_date'): any_value,
                    'warning_text': any_value,
                }
            ),
            extra=PREVENT_EXTRA
        )
    )

    plugin_routing_schema = Any(
        Schema({
            ('deprecation'): Any(deprecation_tombstoning_schema),
            ('tombstone'): Any(deprecation_tombstoning_schema),
            ('redirect'): Any(*string_types),
        }, extra=PREVENT_EXTRA),
    )

    list_dict_plugin_routing_schema = [{str_type: plugin_routing_schema}
                                       for str_type in string_types]

    plugin_schema = Schema({
        ('action'): Any(None, *list_dict_plugin_routing_schema),
        ('become'): Any(None, *list_dict_plugin_routing_schema),
        ('cache'): Any(None, *list_dict_plugin_routing_schema),
        ('callback'): Any(None, *list_dict_plugin_routing_schema),
        ('cliconf'): Any(None, *list_dict_plugin_routing_schema),
        ('connection'): Any(None, *list_dict_plugin_routing_schema),
        ('doc_fragments'): Any(None, *list_dict_plugin_routing_schema),
        ('filter'): Any(None, *list_dict_plugin_routing_schema),
        ('httpapi'): Any(None, *list_dict_plugin_routing_schema),
        ('inventory'): Any(None, *list_dict_plugin_routing_schema),
        ('lookup'): Any(None, *list_dict_plugin_routing_schema),
        ('module_utils'): Any(None, *list_dict_plugin_routing_schema),
        ('modules'): Any(None, *list_dict_plugin_routing_schema),
        ('netconf'): Any(None, *list_dict_plugin_routing_schema),
        ('shell'): Any(None, *list_dict_plugin_routing_schema),
        ('strategy'): Any(None, *list_dict_plugin_routing_schema),
        ('terminal'): Any(None, *list_dict_plugin_routing_schema),
        ('test'): Any(None, *list_dict_plugin_routing_schema),
        ('vars'): Any(None, *list_dict_plugin_routing_schema),
    }, extra=PREVENT_EXTRA)

    # import_redirection schema

    import_redirection_schema = Any(
        Schema({
            ('redirect'): Any(*string_types),
            # import_redirect doesn't currently support deprecation
        }, extra=PREVENT_EXTRA)
    )

    list_dict_import_redirection_schema = [{str_type: import_redirection_schema}
                                           for str_type in string_types]

    # top level schema

    schema = Schema({
        # All of these are optional
        ('plugin_routing'): Any(plugin_schema),
        ('import_redirection'): Any(None, *list_dict_import_redirection_schema),
        # requires_ansible: In the future we should validate this with SpecifierSet
        ('requires_ansible'): Any(*string_types),
        ('action_groups'): dict,
    }, extra=PREVENT_EXTRA)

    # Ensure schema is valid

    try:
        schema(routing)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line/column numbers
            print('%s:%d:%d: %s' % (path, 0, 0, humanize_error(routing, error)))


def main():
    """Validate runtime metadata"""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    collection_legacy_file = 'meta/routing.yml'
    collection_runtime_file = 'meta/runtime.yml'

    for path in paths:
        if path == collection_legacy_file:
            print('%s:%d:%d: %s' % (path, 0, 0, ("Should be called '%s'" % collection_runtime_file)))
            continue

        validate_metadata_file(path, is_ansible=path not in (collection_legacy_file, collection_runtime_file))


if __name__ == '__main__':
    main()
