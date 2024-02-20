# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import functools
import os
from typing import Any, Iterable

import jmespath
import json_merge_patch
import yaml


__all__ = ["ConfigBroker"]


class ConfigBroker(object):
  data: dict

  @classmethod
  def from_configs(cls, configs: Iterable[dict]) -> "ConfigBroker":
    merged_config = functools.reduce(json_merge_patch.merge, reversed(list(configs)), {})
    return cls(merged_config)

  @classmethod
  def from_directory(cls, dirname: str) -> "ConfigBroker":
    configs = []
    for config_path in sorted(os.listdir(dirname)):
      with open(os.path.join(dirname, config_path)) as config_fp:
        if (data := yaml.safe_load(config_fp)) is None:
          continue
        if not isinstance(data, dict):
          raise TypeError(f"Top level of config is not a mapping: {config_fp.name}")
        configs.append(data)
    return cls.from_configs(configs)

  def __init__(self, data: dict):
    self.data = data

  def __contains__(self, name: str) -> bool:
    try:
      self[name]  # pylint: disable=pointless-statement
      return True
    except KeyError:
      return False

  def get(self, name: str, default: Any = None) -> Any:
    try:
      return self[name]
    except KeyError:
      return default

  def __getitem__(self, name: str) -> Any:
    if (value := jmespath.search(name, self.data)) is None:
      raise KeyError(name)
    return value
