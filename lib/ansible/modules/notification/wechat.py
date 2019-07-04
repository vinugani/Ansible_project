#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: lework


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'lework'}

DOCUMENTATION = '''
---
module: wechat
version_added: "1.0"
short_description: Send a message to Qiye Wechat.
description:
   - Send a message to Qiye Wechat.
options:
  corpid:
    description:
      - Business id.
    required: true
  secret:
    description:
      - application secret.
    required: true
  agentid:
    description:
      - application id.
    required: true
  touser:
    description:
      - Member ID list (message recipient, multiple recipients separated by '|', up to 1000). 
      - "Special case: Specify @all to send to all members of the enterprise application."
      -  When toparty, touser, totag is empty, the default value is @all.
  toparty:
    description:
      - A list of department IDs. Multiple recipients are separated by ‘|’ and support up to 100. Ignore this parameter when touser is @all
  totag:
    description:
      - A list of tag IDs, separated by ‘|’ and supported by up to 100. Ignore this parameter when touser is @all
  msg:
    description:
      - The message body.
    required: true
author:
- lework (@lework)
'''

EXAMPLES = '''
# Send all users.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    msg: Ansible task finished
    
# Send a user.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    touser: "LeWork"
    msg: Ansible task finished

# Send multiple user.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    touser: "LeWork|Lework1|Lework2"
    msg: Ansible task finished
    
# Send a department.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    toparty: "10"
    msg: Ansible task finished
'''

RETURN = """
msg:
  description: The message you attempted to send
  returned: success,failure
  type: str
  sample: "Ansible task finished"
touser:
  description: send user id
  returned: success
  type: str
  sample: "ZhangSan"
toparty:
  description: send department id
  returned: success
  type: str
  sample: "10"
totag:
  description: send tag id
  returned: success
  type: str
  sample: "dev"
wechat_error:
  description: Error message gotten from Wechat API
  returned: failure
  type: str
  sample: "Bad Request: message text is empty"
"""


# ===========================================
# WeChat module specific support methods.
#

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url




def main():
    module = AnsibleModule(
        argument_spec=dict(
            corpid=dict(required=True, type='str', no_log=True),
            secret=dict(required=True, type='str', no_log=True),
            agentid=dict(required=True, type='str'),
            msg=dict(required=True, type='str'),
            touser=dict(type='str'),
            toparty=dict(type='str'),
            totag=dict(type='str'),
        ),
        supports_check_mode=True
    )

    corpid = module.params["corpid"]
    secret = module.params["secret"]
    agentid = module.params["agentid"]
    msg = module.params["msg"]
    touser = module.params["touser"]
    toparty = module.params["toparty"]
    totag = module.params["totag"]

    try:
        if not touser and not toparty and not totag:
            touser = "@all"

        wechat = WeChat(module, corpid, secret, agentid)
        wechat.send_message(msg, touser, toparty, totag)

    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % msg, wechat_error=to_native(e), exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, touser=touser, toparty=toparty, totag=totag, msg=msg)

if __name__ == '__main__':
    main()
