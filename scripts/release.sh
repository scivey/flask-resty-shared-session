#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

set -e

function release() {
    pushd ${FLASK_RESTY_ROOT_DIR}
    python setup.py sdist upload
    pushd resty
    luarocks upload --api-key ${LUAROCKS_API_KEY} ./resty-shared-session-0.1.0-1.rockspec
    popd
    popd
}

release
