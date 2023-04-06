# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import functools
import json
import os

import jmespath
import json_merge_patch
import yaml

from sigopt_config.utils import is_mapping


class ConfigBroker(object):
  @classmethod
  def from_configs(cls, configs):
    merged_config = functools.reduce(json_merge_patch.merge, reversed(list(configs)), {})
    return cls(merged_config)

  @classmethod
  def from_directory(cls, dirname):
    configs = []
    for config_path in sorted(os.listdir(dirname)):
      with open(os.path.join(dirname, config_path)) as config_fp:
        configs.append(yaml.safe_load(config_fp))
    return cls.from_configs(configs)

  def __init__(self, data):
    self.data = data

  def _split_name(self, name):
    return name.split(".")

  def __contains__(self, name):
    try:
      self[name]
      return True
    except KeyError:
      return False

  def get(self, name, default=None):
    try:
      return self[name]
    except KeyError:
      return default

  def __getitem__(self, name):
    value = jmespath.search(name, self.data)
    if value is None:
      raise KeyError(name)
    return value
