#!/bin/bash

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

TESTAPP_SCRIPTS_DIR=$(dirname ${BASH_SOURCE[0]})
pushd ${TESTAPP_SCRIPTS_DIR}
TESTAPP_SCRIPTS_DIR=$(pwd)
popd
pushd ${TESTAPP_SCRIPTS_DIR}/..
TESTAPP_ROOT_DIR=$(pwd)
popd

export TESTAPP_SCRIPTS_DIR=${TESTAPP_SCRIPTS_DIR}
export TESTAPP_ROOT_DIR=${TESTAPP_ROOT_DIR}
export TESTAPP_BUILD_DIR=${TESTAPP_ROOT_DIR}/build
export TESTAPP_TEMP_DIR=${TESTAPP_ROOT_DIR}/tmp

export TESTAPP_OPENRESTY_INSTALL_ROOT=/usr/local/openresty
