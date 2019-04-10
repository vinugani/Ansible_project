#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATHS=$PWD/collection_root_user:$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_GATHER_SUBSET=minimal
export ANSIBLE_HOST_PATTERN_MISMATCH=error

# FIXME: just use INVENTORY_PATH as-is once ansible-test sets the right dir
export INVENTORY_PATH=../../$(basename ${INVENTORY_PATH})

# temporary hack to keep this test from running on Python 2.6 in CI
if ansible-playbook pythoncheck.yml | grep UNSUPPORTEDPYTHON; then
  echo skipping test for unsupported Python version...
  exit 0
fi

# test callback
ANSIBLE_CALLBACK_WHITELIST=testns.testcoll.usercallback ansible localhost -m ping | grep "usercallback says ok"

# we need multiple plays, and conditional import_playbook is noisy and causes problems, so choose here which one to use...
[[ ${INVENTORY_PATH} == *.winrm ]] && export TEST_PLAYBOOK=windows.yml || export TEST_PLAYBOOK=posix.yml

# run test playbook
ansible-playbook -i ${INVENTORY_PATH}  -i ./a.statichost.yml -v ${TEST_PLAYBOOK}
