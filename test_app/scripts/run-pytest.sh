#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh


function run-tests() {
    pushd ${TESTAPP_ROOT_DIR}
    py.test -v test_it
    popd
}

run-tests
