#!/usr/bin/env bash

# no_set_e
set -o pipefail

SIGOPT_CONFIG_DIR=$( readlink -f "${1}")
PYTHONPATH="${PYTHONPATH}:${SIGOPT_CONFIG_DIR}/src/python"
PYTHONPATH="${PYTHONPATH}:${SIGOPT_CONFIG_DIR}/test"
export PYTHONPATH
