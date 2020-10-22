#!/usr/bin/env bash

set -x

empty_limit_file="/tmp/limit_file"
touch "${empty_limit_file}"

cleanup() {
    if [[ -f "${empty_limit_file}" ]]; then
            rm -rf "${empty_limit_file}"
    fi
}

trap 'cleanup' EXIT

# https://github.com/ansible/ansible/issues/52152
# Ensure that non-matching limit causes failure with rc 1
ansible-playbook -i ../../inventory --limit foo playbook.yml
if [ "$?" != "1" ]; then
    echo "Non-matching limit should cause failure"
    exit 1
fi

# Ensure that non-existing limit file causes failure with rc 1
ansible-playbook -i ../../inventory --limit @foo playbook.yml
if [ "$?" != "1" ]; then
    echo "Non-existing limit file should cause failure"
    exit 1
fi

set -e

# Ensure that an empty limit does not cause failure with rc 1
ansible-playbook -i ../../inventory --limit @"${empty_limit_file}" playbook.yml

ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook -i ../../inventory "$@" strategy.yml

# test extra vars
ansible-inventory -i testhost, -i ./extra_vars_constructed.yml --list -e 'from_extras=hey ' "$@"|grep '"example": "hellohey"'

# test constructed inventory
ansible-playbook -i ./yaml_inventory.yml -i ./constructed.yml test_constructed_inventory.yml "$@"

# test empty config warns
ANSIBLE_INVENTORY_ENABLED=constructed ansible-inventory -i ./empty_config.yml --list "$@" 2>&1 | grep 'empty_config.yml is empty'
