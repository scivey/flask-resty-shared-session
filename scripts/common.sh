#!/bin/bash

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

FLASK_RESTY_SCRIPTS_DIR=$(dirname ${BASH_SOURCE[0]})
pushd ${FLASK_RESTY_SCRIPTS_DIR}
FLASK_RESTY_SCRIPTS_DIR=$(pwd)
popd
pushd ${FLASK_RESTY_SCRIPTS_DIR}/..
FLASK_RESTY_ROOT_DIR=$(pwd)
popd

export FLASK_RESTY_SCRIPTS_DIR=${FLASK_RESTY_SCRIPTS_DIR}
export FLASK_RESTY_ROOT_DIR=${FLASK_RESTY_ROOT_DIR}
