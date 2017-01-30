#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

set -e

function run-tests() {
    pushd ${FLASK_RESTY_ROOT_DIR}
    py.test -v flask_resty_shared_session/test
    pushd test_app
    ./scripts/run-tests.sh
    popd
    popd
}


run-tests

