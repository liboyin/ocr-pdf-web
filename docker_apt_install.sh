#!/bin/bash

set -euo pipefail

# Configure APT proxy
if [ -v APT_PROXY ]; then
    APT_CONF_PATH=/etc/apt/apt.conf.d/01proxy
    echo "Acquire::http::Proxy \"$APT_PROXY\";" > $APT_CONF_PATH
    cat $APT_CONF_PATH
fi

apt-get update
apt-get install -y --no-install-recommends curl poppler-utils
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
