# (c) 2016, Dag Wieers <dag@wieers.com>
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

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.utils.color import colorize, hostcolor
from collections import OrderedDict

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

import sys

# Design goals:
#
#  + On screen there should only be relevant stuff
#    - How far are we ? (during run, last line)
#    - What issues did we have
#    - What changes have occured
#    - Diff output
#
#  + If verbosity increases, act as default output
#    So that users can easily switch to default for troubleshooting
#
#  + Leave previous task output on screen
#    - If we would clear the line at the start of a task, there would often
#      be no information at all
#
#    - We use the cursor to indicate where in the task we are.
#      Output after the prompt is the output of the previous task
#
#  + Use the same color-conventions of Ansible


# TODO:
#
#  + Ensure all other output is properly displayed
#  + Properly test for terminal capabilities, and fall back to default
#  + Modify Ansible mechanism so we don't need to use sys.stdout directly
#  + Remove items from result to compact the json output when using -v
#  + Make colored output nicer
#  + Find an elegant solution for line wrapping
#  + Support notification handler


# Taken from Dstat
class ansi:
    black = '\033[0;30m'
    darkred = '\033[0;31m'
    darkgreen = '\033[0;32m'
    darkyellow = '\033[0;33m'
    darkblue = '\033[0;34m'
    darkmagenta = '\033[0;35m'
    darkcyan = '\033[0;36m'
    gray = '\033[0;37m'

    darkgray = '\033[1;30m'
    red = '\033[1;31m'
    green = '\033[1;32m'
    yellow = '\033[1;33m'
    blue = '\033[1;34m'
    magenta = '\033[1;35m'
    cyan = '\033[1;36m'
    white = '\033[1;37m'

    blackbg = '\033[40m'
    redbg = '\033[41m'
    greenbg = '\033[42m'
    yellowbg = '\033[43m'
    bluebg = '\033[44m'
    magentabg = '\033[45m'
    cyanbg = '\033[46m'
    whitebg = '\033[47m'

    reset = '\033[0;0m'
    bold = '\033[1m'
    reverse = '\033[2m'
    underline = '\033[4m'

    clear = '\033[2J'
#   clearline = '\033[K'
    clearline = '\033[2K'
#   save = '\033[s'
#   restore = '\033[u'
    save = '\0337'
    restore = '\0338'
    linewrap = '\033[7h'
    nolinewrap = '\033[7l'

    up = '\033[1A'
    down = '\033[1B'
    right = '\033[1C'
    left = '\033[1D'


colors = dict(
    ok=ansi.darkgreen,
    changed=ansi.darkyellow,
    skipped=ansi.darkcyan,
    failed=ansi.darkred,
    unreachable=ansi.redbg+ansi.white
)

states = ( 'skipped', 'ok', 'changed', 'failed', 'unreachable' )

class CallbackModule(CallbackModule_default):

    '''
    This is the dense callback interface, where screen estate is still valued.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'dense'

    def __init__(self):

        # From CallbackModule
        self._display = display

        if self._display.verbosity >= 4:
            name = getattr(self, 'CALLBACK_NAME', 'unnamed')
            ctype = getattr(self, 'CALLBACK_TYPE', 'old')
            version = getattr(self, 'CALLBACK_VERSION', '1.0')
            self._display.vvvv('Loaded callback %s of type %s, v%s' % (name, ctype, version))

        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()

        # When using -vv or higher, simply do the default action
        if self._display.verbosity >= 2:
            return

        self.hosts = OrderedDict()
        self.keep = False
        self.shown_title = False
        self.playnr = 0
        self.tasknr = 0
        self.handlernr = 0

        # Start immediately on the first line
        sys.stdout.write(ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()
 
    def _add_host(self, result, status):
        name = result._host.get_name()

        # Check if we have to update an existing state (when looping)
        if name not in self.hosts:
            self.hosts[name] = status
        elif states.index(self.hosts[name]) < states.index(status):
            self.hosts[name] = status

        self._display_progress(result)

        if status in ['changed', 'failed', 'unreachable']:
            # Ensure that tasks with changes/failures stay on-screen
            self.keep = True

            if self._display.verbosity == 1:
                # Print task title, if needed
                self._display_task_banner()

                # TODO: clean up result output, eg. remove changed, delta, end, start, ...
                if status == 'changed':
                    self.super_ref.v2_runner_on_ok(result)
                elif status == 'failed':
                    self.super_ref.v2_runner_on_failed(result)
                elif status == 'unreachable':
                    self.super_ref.v2_runner_on_unreachable(result)

    def _display_task_banner(self):
        if not self.shown_title:
            self.shown_title = True
            sys.stdout.write(ansi.restore + ansi.clearline)
            sys.stdout.write(ansi.underline + 'task %d: %s' % (self.tasknr, self.task.get_name().strip()))
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
            sys.stdout.flush()
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)

    def _display_progress(self, result):
        # Always rewrite the complete line
        sys.stdout.write(ansi.restore + ansi.clearline + ansi.underline)
        sys.stdout.write('task %d:' % self.tasknr)
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

        # Print delegated hostname, if needed
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            sys.stdout.write(' ' + delegated_vars['ansible_host'] + '>>')

        # Print out each host with its own status-color
        for name in self.hosts:
            sys.stdout.write(' ' + colors[self.hosts[name]] + name + ansi.reset)
            sys.stdout.flush()

        # Reset color
        sys.stdout.write(ansi.reset)

    def v2_playbook_on_play_start(self, play):
        if self._display.verbosity > 1:
            self.super_ref.v2_playbook_on_play_start(play)
            return

        # Reset counters at the start of each play
        self.tasknr = 0
        self.handlernr = 0
        self.playnr += 1
        self.play = play

        # Leave the previous task on screen (as it has changes/errors)
        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline + ansi.bold)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline + ansi.bold)

        # Write the next play on screen IN UPPERCASE, and make it permanent
        name = play.get_name().strip()
        if not name:
            name = 'unnamed'
        sys.stdout.write('PLAY %d: %s' % (self.playnr, name.upper()))
        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self._display.verbosity > 1:
            self.super_ref.v2_playbook_on_task_start(task, is_conditional)
            return

        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline + ansi.underline)
        else:
            sys.stdout.write(ansi.restore + ansi.underline)

        # Reset counters at the start of each task
        self.keep = False
        self.shown_title = False
        self.hosts = OrderedDict()
        self.task = task

        # Enumerate task if not setup (task names are too long for dense output)
        if task.get_name() != 'setup':
            self.tasknr += 1

        # Write the next task on screen (behind the prompt is the previous output)
        sys.stdout.write('task %d.' % self.tasknr)
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()
#        self._display_progress()

    def v2_playbook_on_handler_task_start(self, task):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_on_handler_task_start(task)
            return

        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline + ansi.underline)
        else:
            sys.stdout.write(ansi.restore + ansi.reset + ansi.underline)

        # Reset counters at the start of each handler
        self.keep = False
        self.shown_title = False
        self.hosts = OrderedDict()
        self.task = task

        # Write the next task on screen (behind the prompt is the previous output)
        sys.stdout.write('handler %d.' % self.handlernr)
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()
#        self._display_progress()

    def v2_playbook_on_cleanup_task_start(self, task):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_on_cleanup_task_start(start)
            return

        self._display.banner("CLEANUP TASK [%s]" % task.get_name().strip())

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if self._display.verbosity >= 2:
            self.super_ref.v2_runner_on_failed(result, ignore_errors)
            return

        self._add_host(result, 'failed')

    def v2_runner_on_ok(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_runner_on_ok(result)
            return

        if result._result.get('changed', False):
            self._add_host(result, 'changed')
        else:
            self._add_host(result, 'ok')

    def v2_runner_on_skipped(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_runner_on_skipped(result)
            return

        self._add_host(result, 'skipped')

    def v2_runner_on_unreachable(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_runner_on_unreachable(result)
            return

        self._add_host(result, 'unreachable')

    def v2_runner_on_include(self, included_file):
        if self._display.verbosity >= 2:
            self.super_ref.v2_runner_on_include(included_file)

    def v2_playbook_item_on_ok(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_item_on_ok(result)

        if result._result.get('changed', False):
            self._add_host(result, 'changed')
        else:
            self._add_host(result, 'ok')

    def v2_playbook_item_on_failed(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_item_on_failed(result)

        self._add_host(result, 'failed')

    def v2_playbook_item_on_skipped(self, result):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_item_on_skipped(result)

        self._add_host(result, 'skipped')

    def v2_playbook_on_no_hosts_remaining(self):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_on_no_hosts_remaining()
            return

        # TBD
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)

        self.keep = False

        sys.stdout.write(ansi.white + ansi.redbg + 'NO MORE HOSTS LEFT' + ansi.reset)
        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

    def v2_playbook_on_stats(self, stats):
        if self._display.verbosity >= 2:
            self.super_ref.v2_playbook_on_stats(stats)
            return

        # In normal mode screen output should be sufficient
        elif self._display.verbosity == 0:
            return

        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline + ansi.bold)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline + ansi.bold)

        sys.stdout.write('SUMMARY')

        # FIXME: Reports 'module' object C not having attribute 'COLOR_OK' ?? Doing default instead :-/
        self.super_ref.v2_playbook_on_stats(stats)
        return

        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )