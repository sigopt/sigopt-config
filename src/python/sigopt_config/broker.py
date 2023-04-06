# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import functools
import json
import os

import json_merge_patch
import yaml

from sigopt_config.source import (
  ConfigBrokerSource,
)
from sigopt_config.utils import extend_dict, is_mapping, user_input_to_bool


_NO_DEFAULT = object()


class ConfigBroker(object):
  def __init__(self, source):
    assert isinstance(source, ConfigBrokerSource), error_message
    self.source = source
    self.impl = ConfigBrokerImpl(self.source)

  def get(self, name, default=None):
    return self.impl.get(name, default)

  def get_object(self, name, default=None):
    return self.impl.get_object(name, default)

  @classmethod
  def from_configs(cls, configs):
    merged_config = functools.reduce(json_merge_patch.merge, reversed(list(configs)), {})
    source = ConfigBrokerSource(merged_config)
    broker = cls(source)
    return broker

  @classmethod
  def from_directory(cls, dirname):
    configs = []
    for config_path in sorted(os.listdir(dirname)):
      with open(os.path.join(dirname, config_path)) as config_fp:
        configs.append(yaml.safe_load(config_fp))
    return cls.from_configs(configs)

  def __getitem__(self, name):
    ret = self.impl.get(name, _NO_DEFAULT)
    if ret == _NO_DEFAULT:
      raise KeyError(name)
    return ret


class ConfigBrokerImpl(object):
  def __init__(self, sources):
    self.sources = sources

  def get(self, name, default):
    return self._get(name, default)[0]

  def _get(self, name, default):
    for source in self.sources:
      if name in source:
        ret = source.get(name, default)
        self._ensure_safe_return(ret)
        return ret, source
    return default, None

  def get_object(self, name, default):
    objs = []
    for source in self.sources:
      if name in source:
        our_default = object()
        ret = source.get(name, our_default)
        assert ret is not our_default
        objs.append(ret)
    return extend_dict({}, *reversed(objs)) if objs else default

  def _ensure_safe_return(self, val):
    if is_mapping(val):
      raise Exception("Possibly unsafe .get of JSON object, values might be missing. Please use .get_object instead")
