#!/bin/bash

set -euo pipefail

# Configure PyPI proxy if defined
if [ -v PYPI_PROXY ]; then
    PIP_CONF_PATH=$HOME/.pip/pip.conf
    mkdir -p "$(dirname "$PIP_CONF_PATH")"
    cat <<EOF > "$PIP_CONF_PATH"
[global]
index-url = $PYPI_PROXY
trusted-host = $(echo "$PYPI_PROXY" | sed -E 's|https?://([^:/]+).*|\1|')
EOF
    cat "$PIP_CONF_PATH"
fi

PIP_NO_CACHE_DIR=1 pipx install streamlit
