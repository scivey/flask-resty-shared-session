#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

set -e

function bad-dir() {
    echo "bad dir: '${1}'" >&2
    exit 1
}

function clean-py-dir() {
    local target="$1"
    if [[ "${target}" == "" ]]; then
        bad-dir ${target}
        return
    elif [[ ! -d "${target}" ]]; then
        bad-dir ${target}
        return
    fi
    find $target -name "*.pyc" -exec rm -f {} +
    find $target -name "__pycache__" -exec rm -rf {} +
}

function clean-all() {
    pushd ${FLASK_RESTY_ROOT_DIR}
    clean-py-dir flask_resty_shared_session
    clean-py-dir test_app/app_server
    clean-py-dir test_app/test_it
    rm -rf .cache test_app/.cache dist *.egg-info
    rm -rf test_app/tmp
    popd
}

clean-all
