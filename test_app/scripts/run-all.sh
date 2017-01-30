#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh


function run-all() {
    pushd ${TESTAPP_ROOT_DIR}
    local scripts=${TESTAPP_SCRIPTS_DIR}
    export PYTHONUNBUFFERED="Yay"
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    ${scripts}/run-app.sh &
    ${scripts}/run-resty.sh &
    trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM SIGKILL EXIT
    wait
    popd
}

run-all
