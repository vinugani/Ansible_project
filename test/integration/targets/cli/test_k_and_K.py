#!/usr/bin/env python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import pexpect

os.environ['ANSIBLE_NOCOLOR'] = '1'

out = pexpect.run(
    'ansible -c ssh -i localhost, -u cliuser1 -e ansible_python_interpreter=/usr/bin/python3 -m command -a whoami -Kkb --become-user cliuser2 localhost',
    events={
        'SSH password:': 'secretpassword\n',
        'BECOME password': 'secretpassword\n',
    },
    timeout=10
)

print(out)

assert b'cliuser2' in out
