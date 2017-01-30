#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

set -e

function release() {
    pushd ${FLASK_RESTY_ROOT_DIR}
    python setup.py sdist upload
    luarocks --api-key ${LUAROCKS_API_KEY} upload ./resty/resty-shared-session-0.1.0-1.rockspec
    popd
}


release
