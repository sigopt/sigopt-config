# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections import abc


def is_mapping(obj):
  return isinstance(obj, abc.Mapping)


def extend_dict(base, *dicts):
  assert is_mapping(base)
  for d in dicts:
    assert is_mapping(d)
    base.update(d)
  return base


def user_input_to_bool(i):
  if i in ("True", "true", True):
    return True
  if i in ("False", "false", False):
    return False
  raise ValueError(f"{i} is not a valid boolean")
