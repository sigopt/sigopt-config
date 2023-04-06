# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import abc


def is_mapping(obj):
  return isinstance(obj, abc.Mapping)
