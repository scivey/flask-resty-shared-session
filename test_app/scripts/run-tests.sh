#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh


function run-all() {
    pushd ${TESTAPP_ROOT_DIR}
    local tmp_dir="${TESTAPP_ROOT_DIR}/tmp"
    local test_logs_dir="${tmp_dir}/test_logs"
    mkdir -p ${test_logs_dir}
    local resty_log="${test_logs_dir}/resty.log"
    local flask_log="${test_logs_dir}/flask.log"

    echo "flask will log to ${flask_log}" >&2
    echo "resty will log to ${resty_log}" >&2

    local scripts=${TESTAPP_SCRIPTS_DIR}
    export PYTHONUNBUFFERED="Yay"
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM SIGKILL EXIT

    ${scripts}/run-app.sh &> ${flask_log} &
    local app_pid="$!"
    ${scripts}/run-resty.sh &> ${resty_log} &
    local resty_pid="$!"

    sleep 0.1
    ${scripts}/run-pytest.sh &
    local tests_pid="$!"

    wait ${tests_pid}

    kill -9 ${app_pid}
    kill -9 ${resty_pid}
    wait
    popd
}

run-all
