#!/usr/bin/env bash
# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

# no_set_e
set -o pipefail

SIGOPT_CONFIG_DIR=$( readlink -f "${1}")
PYTHONPATH="${PYTHONPATH}:${SIGOPT_CONFIG_DIR}/src/python"
PYTHONPATH="${PYTHONPATH}:${SIGOPT_CONFIG_DIR}/test"
export PYTHONPATH
