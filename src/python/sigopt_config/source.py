# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

from sigopt_config.utils import is_mapping


class ConfigBrokerSource(object):
  def __init__(self, d):
    self.d = d

  def _split_name(self, name):
    return name.split(".")

  def __contains__(self, name):
    try:
      self._do_get(name)
      return True
    except KeyError:
      return False

  def get(self, name, default=None):
    try:
      return self._do_get(name)
    except KeyError:
      return default

  def _do_get(self, name):
    base_dict = self.d
    parts = self._split_name(name)

    for p in parts[:-1]:
      base_dict = base_dict.get(p)
      if not is_mapping(base_dict):
        raise KeyError(name)

    if is_mapping(base_dict):
      try:
        return base_dict[parts[-1]]
      except KeyError as ke:
        raise KeyError(name) from ke

    raise KeyError(name)
