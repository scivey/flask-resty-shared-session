#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

pushd ${TESTAPP_ROOT_DIR}

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM SIGKILL EXIT
export PYTHONUNBUFFERED="Yay"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m app_server.application
