#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: cyberark_user
short_description: Module for CyberArk User Management using PAS Web Services SDK
author: Edward Nunez @ CyberArk BizDev (@enunez-cyberark, @cyberark-bizdev, @erasmix)
version_added: 2.4
description:
    - CyberArk User Management using PAS Web Services SDK. It currently supports the following
      actions Get User Details, Add User, Update User, Delete User.


options:
    username:
        required: True
        description:
            - The name of the user who will be queried (for details), added, updated or deleted.
    state:
        default: present
        choices: [present, absent]
        description:
            - Specifies the state needed for the user
              present for create user, absent for delete user.
    cyberark_session:
        required: True
        description:
            - Dictionary set by a CyberArk authentication containing the different values to perform actions on a logged-on CyberArk session,
              please see M(cyberark_authentication) module for an example of cyberark_session.
    initial_password:
        description:
            - The password that the new user will use to log on the first time. This password must meet the password policy requirements.
              this parameter is required when state is present -- Add User.
    new_password:
        description:
            - The user updated password. Make sure that this password meets the password policy requirements.
    email:
        description:
            - The user email address.
    first_name:
        description:
            - The user first name.
    last_name:
        description:
            - The user last name.
    change_password_on_the_next_logon:
        type: bool
        default: 'no'
        description:
            - Whether or not the user must change their password in their next logon.
              Valid values = true/false.
    expiry_date:
        description:
            - The date and time when the user account will expire and become disabled.
    user_type_name:
        default: EPVUser
        description:
            - The type of user.
    disabled:
        type: bool
        default: 'no'
        description:
            - Whether or not the user will be disabled. Valid values = true/false.
    location:
        description:
            - The Vault Location for the user.
    group_name:
        description:
            - The name of the group the user will be added to.
'''

EXAMPLES = '''
- name: Logon to CyberArk Vault using PAS Web Services SDK
  cyberark_authentication:
    api_base_url: "https://components.cyberark.local"
    use_shared_logon_authentication: true

- name: Create user & immediately add it to a group
  cyberark_user:
    username: "username"
    initial_password: "password"
    user_type_name: "EPVUser"
    change_password_on_the_next_logon: false
    group_name: "GroupOfUsers"
    state: present
    cyberark_session: "{{ cyberark_session }}"

- name: Make sure user is present and reset user credential if present
  cyberark_user:
    username: "Username"
    new_password: "password"
    disabled: false
    state: present
    cyberark_session: "{{ cyberark_session }}"

- name: Logoff from CyberArk Vault
  cyberark_authentication:
    state: absent
    cyberark_session: "{{ cyberark_session }}"
'''

RETURN = '''
changed:
    description: Whether there was a change done.
    type: bool
    returned: always
cyberark_user:
    description: Dictionary containing result properties.
    returned: always
    type: dict
    sample:
        result:
            description: user properties when state is present
            type: dict
            returned: success
status_code:
    description: Result HTTP Status code
    returned: success
    type: int
    sample: 200
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves import http_client as httplib
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url


def user_details(module):

    # Get username from module parameters, and api base url
    # along with validate_certs from the cyberark_session established
    username = module.params["username"]
    cyberark_session = module.params["cyberark_session"]
    api_base_url = cyberark_session["api_base_url"]
    validate_certs = cyberark_session["validate_certs"]

    # Prepare result, end_point, and headers
    result = {}
    end_point = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}".format(
        username)
    headers = {'Content-Type': 'application/json'}
    headers["Authorization"] = cyberark_session["token"]

    try:

        response = open_url(
            api_base_url + end_point,
            method="GET",
            headers=headers,
            validate_certs=validate_certs)
        result = {"result": json.loads(response.read())}

        return (False, result, response.getcode())

    except (HTTPError, httplib.HTTPException) as http_exception:

        if http_exception.code == 404:
            return (False, None, http_exception.code)
        else:
            module.fail_json(
                msg=("Error while performing user_details."
                     "Please validate parameters provided."
                     "\n*** end_point=%s%s\n ==> %s" % (api_base_url, end_point, to_text(http_exception))),
                headers=headers,
                status_code=http_exception.code)

    except Exception as unknown_exception:

        module.fail_json(
            msg=("Unknown error while performing user_details."
                 "\n*** end_point=%s%s\n%s" % (api_base_url, end_point, to_text(unknown_exception))),
            headers=headers,
            exception=traceback.format_exc(),
            status_code=-1)


def user_add_or_update(module, HTTPMethod):

    # Get username from module parameters, and api base url
    # along with validate_certs from the cyberark_session established
    username = module.params["username"]
    cyberark_session = module.params["cyberark_session"]
    api_base_url = cyberark_session["api_base_url"]
    validate_certs = cyberark_session["validate_certs"]

    # Prepare result, paylod, and headers
    result = {}
    payload = {}
    headers = {'Content-Type': 'application/json',
               "Authorization": cyberark_session["token"]}

    # end_point and payload sets different depending on POST/PUT
    # for POST -- create -- payload contains username
    # for PUT -- update -- username is part of the endpoint
    if HTTPMethod == "POST":
        end_point = "/PasswordVault/WebServices/PIMServices.svc/Users"
        payload["UserName"] = username
    elif HTTPMethod == "PUT":
        end_point = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}"
        end_point = end_point.format(username)

    # --- Optionally populate payload based on parameters passed ---
    if "initial_password" in module.params:
        payload["InitialPassword"] = module.params["initial_password"]

    if "new_password" in module.params:
        payload["NewPassword"] = module.params["new_password"]

    if "email" in module.params:
        payload["Email"] = module.params["email"]

    if "first_name" in module.params:
        payload["FirstName"] = module.params["first_name"]

    if "last_name" in module.params:
        payload["LastName"] = module.params["last_name"]

    if "change_password_on_the_next_logon" in module.params:
        if module.params["change_password_on_the_next_logon"]:
            payload["ChangePasswordOnTheNextLogon"] = "true"
        else:
            payload["ChangePasswordOnTheNextLogon"] = "false"

    if "expiry_date" in module.params:
        payload["ExpiryDate"] = module.params["expiry_date"]

    if "user_type_name" in module.params:
        payload["UserTypeName"] = module.params["user_type_name"]

    if "disabled" in module.params:
        if module.params["disabled"]:
            payload["Disabled"] = "true"
        else:
            payload["Disabled"] = "false"

    if "location" in module.params:
        payload["Location"] = module.params["location"]
    # --------------------------------------------------------------

    try:

        # execute REST action
        response = open_url(
            api_base_url + end_point,
            method=HTTPMethod,
            headers=headers,
            data=json.dumps(payload),
            validate_certs=validate_certs)

        result = {"result": json.loads(response.read())}

        return (True, result, response.getcode())

    except (HTTPError, httplib.HTTPException) as http_exception:

        module.fail_json(
            msg=("Error while performing user_add_or_update."
                 "Please validate parameters provided."
                 "\n*** end_point=%s%s\n ==> %s" % (api_base_url, end_point, to_text(http_exception))),
            payload=payload,
            headers=headers,
            status_code=http_exception.code)

    except Exception as unknown_exception:

        module.fail_json(
            msg=("Unknown error while performing user_add_or_update."
                 "\n*** end_point=%s%s\n%s" % (api_base_url, end_point, to_text(unknown_exception))),
            payload=payload,
            headers=headers,
            exception=traceback.format_exc(),
            status_code=-1)


def user_delete(module):

    # Get username from module parameters, and api base url
    # along with validate_certs from the cyberark_session established
    username = module.params["username"]
    cyberark_session = module.params["cyberark_session"]
    api_base_url = cyberark_session["api_base_url"]
    validate_certs = cyberark_session["validate_certs"]

    # Prepare result, end_point, and headers
    result = {}
    end_point = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}".format(
        username)

    headers = {'Content-Type': 'application/json'}
    headers["Authorization"] = cyberark_session["token"]

    try:

        # execute REST action
        response = open_url(
            api_base_url + end_point,
            method="DELETE",
            headers=headers,
            validate_certs=validate_certs)

        result = {"result": {}}

        return (True, result, response.getcode())

    except (HTTPError, httplib.HTTPException) as http_exception:

        exception_text = to_text(http_exception)
        if http_exception.code == 404 and "ITATS003E" in exception_text:
            # User does not exist
            result = {"result": {}}
            return (False, result, http_exception.code)
        else:
            module.fail_json(
                msg=("Error while performing user_delete."
                     "Please validate parameters provided."
                     "\n*** end_point=%s%s\n ==> %s" % (api_base_url, end_point, exception_text)),
                headers=headers,
                status_code=http_exception.code)

    except Exception as unknown_exception:

        module.fail_json(
            msg=("Unknown error while performing user_delete."
                 "\n*** end_point=%s%s\n%s" % (api_base_url, end_point, to_text(unknown_exception))),
            headers=headers,
            exception=traceback.format_exc(),
            status_code=-1)


def user_add_to_group(module):

    # Get username, and groupname from module parameters, and api base url
    # along with validate_certs from the cyberark_session established
    username = module.params["username"]
    group_name = module.params["group_name"]
    cyberark_session = module.params["cyberark_session"]
    api_base_url = cyberark_session["api_base_url"]
    validate_certs = cyberark_session["validate_certs"]

    # Prepare result, end_point, headers and payload
    result = {}
    end_point = "/PasswordVault/WebServices/PIMServices.svc//Groups/{0}/Users".format(
        group_name)

    headers = {'Content-Type': 'application/json'}
    headers["Authorization"] = cyberark_session["token"]
    payload = {"UserName": username}

    try:

        # execute REST action
        response = open_url(
            api_base_url + end_point,
            method="POST",
            headers=headers,
            data=json.dumps(payload),
            validate_certs=validate_certs)

        result = {"result": {}}

        return (True, result, response.getcode())

    except (HTTPError, httplib.HTTPException) as http_exception:

        exception_text = to_text(http_exception)
        if http_exception.code == 409 and "ITATS262E" in exception_text:
            # User is already member of Group
            return (False, None, http_exception.code)
        else:
            module.fail_json(
                msg=("Error while performing user_add_to_group."
                     "Please validate parameters provided."
                     "\n*** end_point=%s%s\n ==> %s" % (api_base_url, end_point, exception_text)),
                payload=payload,
                headers=headers,
                exception=traceback.format_exc(),
                status_code=http_exception.code)

    except Exception as unknown_exception:

        module.fail_json(
            msg=("Unknown error while performing user_add_to_group."
                 "\n*** end_point=%s%s\n%s" % (api_base_url, end_point, to_text(unknown_exception))),
            payload=payload,
            headers=headers,
            status_code=-1)


def main():

    fields = {
        "username": {"required": True, "type": "str"},
        "state": {"type": "str",
                  "choices": ["present", "absent"],
                  "default": "present"},
        "cyberark_session": {"required": True, "type": "dict"},
        "initial_password": {"type": "str", "no_log": True},
        "new_password": {"type": "str", "no_log": True},
        "email": {"type": "str"},
        "first_name": {"type": "str"},
        "last_name": {"type": "str"},
        "change_password_on_the_next_logon": {"type": "bool"},
        "expiry_date": {"type": "str"},
        "user_type_name": {"type": "str"},
        "disabled": {"type": "bool"},
        "location": {"type": "str"},
        "group_name": {"type": "str"},
    }

    module = AnsibleModule(argument_spec=fields)

    state = module.params["state"]

    changed = False
    result = {}

    if (state == "present"):
        (changed, result, status_code) = user_details(module)
        if (status_code == 200):  # user already exists
            if ("new_password" in module.params):
                # if new_password specified, proceed to update user credential
                (changed, result, status_code) = user_add_or_update(module, "PUT")
            if ("group_name" in module.params and module.params["group_name"] is not None):
                # if user exists, add to group if needed
                (changed, ignored_result, ignored_status_code) = user_add_to_group(module)
        elif (status_code == 404):
            # user does not exist, proceed to create it
            (changed, result, status_code) = user_add_or_update(module, "POST")
            if (status_code == 201 and "group_name" in module.params and module.params["group_name"] is not None):
                # if user was created, add to group if needed
                (changed, ignored_result, ignored_status_code) = user_add_to_group(module)
    elif (state == "absent"):
        (changed, result, status_code) = user_delete(module)

    module.exit_json(
        changed=changed,
        cyberark_user=result,
        status_code=status_code)


if __name__ == '__main__':
    main()
