#!/usr/bin/env bash

set -e
set -o pipefail

SIGOPT_CONFIG_DIR=$( dirname "${BASH_SOURCE[0]}" )
source "${SIGOPT_CONFIG_DIR}/tools/set_python_path.sh" "${SIGOPT_CONFIG_DIR}"
exec -- "$@"
