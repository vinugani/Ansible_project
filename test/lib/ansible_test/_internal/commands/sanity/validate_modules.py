"""Sanity test using validate-modules."""
from __future__ import annotations

import collections
import json
import os
import typing as t

from . import (
    DOCUMENTABLE_PLUGINS,
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SANITY_ROOT,
)

from ...test import (
    TestResult,
)

from ...target import (
    TestTarget,
)

from ...util import (
    SubprocessError,
    display,
)

from ...util_common import (
    run_command,
)

from ...ansible_util import (
    ansible_environment,
    get_collection_detail,
    CollectionDetailError,
)

from ...config import (
    SanityConfig,
)

from ...ci import (
    get_ci_provider,
)

from ...data import (
    data_context,
)

from ...host_configs import (
    PythonConfig,
)


class ValidateModulesTest(SanitySingleVersion):
    """Sanity test using validate-modules."""

    def __init__(self):
        super().__init__()

        self.optional_error_codes.update([
            'deprecated-date',
        ])

        content = data_context().content
        self._prefixes = {
            plugin_type: plugin_path + '/'
            for plugin_type, plugin_path in content.plugin_paths.items()
            if plugin_type != 'modules' and plugin_type in DOCUMENTABLE_PLUGINS
        }
        self._exclusions = {os.path.join(prefix, '__init__.py') for prefix in self._prefixes.values()}
        if not data_context().content.collection:
            self._exclusions.add('lib/ansible/plugins/cache/base.py')

    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'A100'

    def get_plugin_type(self, target):  # type: (TestTarget) -> t.Optional[str]
        """Return the plugin type of the given target, or None if it is neither a plugin or module."""
        if target.path in self._exclusions:
            return None
        if target.module:
            return 'module'
        for plugin_type, prefix in self._prefixes.items():
            if target.path.startswith(prefix):
                return plugin_type
        return None

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if self.get_plugin_type(target) is not None]

    def test(self, args, targets, python):  # type: (SanityConfig, SanityTargets, PythonConfig) -> TestResult
        env = ansible_environment(args, color=False)

        settings = self.load_processor(args)

        target_per_type = collections.defaultdict(list)
        for target in targets.include:
            target_per_type[self.get_plugin_type(target)].append(target)

        cmd = [
            python.path,
            os.path.join(SANITY_ROOT, 'validate-modules', 'validate-modules'),
            '--format', 'json',
            '--arg-spec',
        ]

        if data_context().content.collection:
            cmd.extend(['--collection', data_context().content.collection.directory])

            try:
                collection_detail = get_collection_detail(args, python)

                if collection_detail.version:
                    cmd.extend(['--collection-version', collection_detail.version])
                else:
                    display.warning('Skipping validate-modules collection version checks since no collection version was found.')
            except CollectionDetailError as ex:
                display.warning('Skipping validate-modules collection version checks since collection detail loading failed: %s' % ex.reason)
        else:
            base_branch = args.base_branch or get_ci_provider().get_base_branch()

            if base_branch:
                cmd.extend([
                    '--base-branch', base_branch,
                ])
            else:
                display.warning('Cannot perform module comparison against the base branch because the base branch was not detected.')

        errors = []
        for plugin_type, plugin_targets in sorted(target_per_type.items()):
            paths = [target.path for target in plugin_targets]
            plugin_cmd = list(cmd)
            if plugin_type != 'module':
                plugin_cmd += ['--plugin-type', plugin_type]
            plugin_cmd += paths

            try:
                stdout, stderr = run_command(args, plugin_cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr or status not in (0, 3):
                raise SubprocessError(cmd=plugin_cmd, status=status, stderr=stderr, stdout=stdout)

            if args.explain:
                continue

            messages = json.loads(stdout)

            plugin_errors = []
            for filename in messages:
                output = messages[filename]

                for item in output['errors']:
                    plugin_errors.append(SanityMessage(
                        path=filename,
                        line=int(item['line']) if 'line' in item else 0,
                        column=int(item['column']) if 'column' in item else 0,
                        code='%s' % item['code'],
                        message=item['msg'],
                    ))

            plugin_errors = settings.process_errors(plugin_errors, paths)
            errors += plugin_errors

        if args.explain:
            return SanitySuccess(self.name)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
