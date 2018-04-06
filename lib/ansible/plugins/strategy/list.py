# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    strategy: list
    short_description: Lists playbook's tasks and/or hosts
    description:
        - Does not execute Tasks, used for the CLI --list options.
    version_added: "2.6"
    author: Ansible Core Team
'''

from ansible.executor.task_result import TaskResult
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule


class StrategyModule(LinearStrategyModule):

    queue = []

    def _execute_meta(self, task, play_context, iterator, host):
        return [TaskResult(host, task, {})]

    def _queue_task(self, host, task, task_vars, play_context):
        self.queue.append((host, task))

    def _process_pending_results(self, iterator, max_passes):

        results = []
        while self.queue:
            (host, task) = self.queue.pop()
            tr = TaskResult(host, task, {})
            self._tqm.send_callback('v2_runner_on_ok', tr)
            results.append(tr)

        opts = {'tasks':  getattr(self._tqm._options, 'listtasks', False),
                'tags':  getattr(self._tqm._options, 'listtags', False),
                'hosts':  getattr(self._tqm._options, 'listhosts', False)}
        self._tqm.send_callback('list_options', opts)

        return results
