#!/bin/bash

. $(dirname ${BASH_SOURCE[0]})/common.sh

pushd ${TESTAPP_ROOT_DIR}
mkdir -p tmp/logs
pushd tmp

rm -f sitelib local_resty
ln -s ${TESTAPP_ROOT_DIR}/resty_conf/sitelib sitelib
ln -s ${TESTAPP_ROOT_DIR}/../resty/lib/resty local_resty


CACHE_DIRS="group_cache"
for dname in $CACHE_DIRS; do
    rm -rf $dname && mkdir -p $dname
done
RESTY_PORT="8089"
echo "${BASH_SOURCE[0]} starting: cwd='$(pwd)' port=${RESTY_PORT}" >&2
SUCCESS=0

for i in $(seq 0 100); do
    outcome=$(nc -vz 127.0.0.1 ${RESTY_PORT} &> /dev/null)
    status=$?
    # we want the port check to fail -- that means nothing is listening.
    if [[ "${status}" == "0" ]]; then
        sleep 0.05
        continue
    fi
    SUCCESS="1"
    break
done

if [[ "${SUCCESS}" == "1" ]]; then
    RESTY_BINS=${TESTAPP_OPENRESTY_INSTALL_ROOT}/nginx/sbin
    export PATH=${RESTY_BINS}:${PATH}
    exec nginx -p `pwd` -c ../resty_conf/nginx.conf
else
    echo "port ${RESTY_PORT} was already in use.." >&2
    exit 1
fi
