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
  DictConfigBrokerSource,
)
from sigopt_config.utils import extend_dict, is_mapping, user_input_to_bool


_NO_DEFAULT = object()
DEFAULT_SIGOPT_CONFIG_ENV_KEY = "sigopt_api_config_file"
DEFAULT_SIGOPT_CONFIG_DIR = "./config"
SIGOPT_CONFIG_DIR_ENV_KEY = "sigopt_api_config_dir"


class ConfigBroker(object):
  def __init__(self, sources):
    error_message = (
      "Sources must be a list of ConfigBrokerSources. Hint: you might want one of the ConfigBroker.from_* classmethods"
    )
    assert isinstance(sources, list), error_message
    sources = [source for source in sources if source]
    assert all(isinstance(source, ConfigBrokerSource) for source in sources), error_message
    self.sources = sources
    self.impl = ConfigBrokerImpl(self.sources)

  def get(self, name, default=None):
    return self.impl.get(name, default)

  def get_object(self, name, default=None):
    return self.impl.get_object(name, default)

  def get_array(self, name, default=None):
    return self.impl.get_array(name, default)

  def get_int(self, name, default=None):
    return self.impl.get_int(name, default)

  def get_bool(self, name, default=None):
    return self.impl.get_bool(name, default)

  def get_string(self, name, default=None):
    return self.impl.get_string(name, default)

  @classmethod
  def from_configs(cls, configs):
    configs = [configs] if is_mapping(configs) else configs
    merged_config = functools.reduce(json_merge_patch.merge, reversed(configs), {})
    sources = [
      DictConfigBrokerSource(merged_config),
    ]
    broker = cls(sources)
    return broker

  @classmethod
  def from_directory(cls, dirname):
    configs = []
    for config_path in sorted(os.listdir(dirname)):
      with open(os.path.join(dirname, config_path)) as config_fp:
        configs.append(yaml.safe_load(config_fp))
    return cls.from_configs(configs)

  @classmethod
  def from_file(cls, filename):
    configs = []
    extends = filename
    while extends:
      extends = os.path.abspath(extends)
      try:
        with open(extends, "r") as config_fp:
          config = json.load(config_fp)
      except OSError as ose:
        raise Exception(f"Error when loading config file {extends}") from ose
      original = extends
      extends = config.pop("extends", None)
      assert isinstance(
        extends, (str, type(None))
      ), f"The extends section for {original} should be a string, got {type(extends).__name__}"
      configs.append(config)
      if extends is not None:
        basedir = os.environ.get(SIGOPT_CONFIG_DIR_ENV_KEY, DEFAULT_SIGOPT_CONFIG_DIR)
        if extends.startswith("./") or extends.startswith("../"):
          basedir = os.path.dirname(original)
        extends = os.path.join(basedir, extends)
    return cls.from_configs(configs)

  @classmethod
  def from_environ(cls, env_var=DEFAULT_SIGOPT_CONFIG_ENV_KEY):
    config_file = os.environ[env_var]
    return cls.from_file(config_file)

  def __getitem__(self, name):
    ret = self.impl.get(name, _NO_DEFAULT)
    if ret == _NO_DEFAULT:
      raise KeyError(name)
    return ret

  def __setitem__(self, name, value):
    self.impl.set_item(name, value)


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

  def get_int(self, name, default):
    return self._typed_get(name, default, int)

  def get_bool(self, name, default):
    return self._typed_get(name, default, bool, user_input_to_bool)

  def get_string(self, name, default):
    return self._typed_get(name, default, str, str)

  def get_array(self, name, default):
    return self._typed_get(name, default, list)

  def _typed_get(self, name, default, typ, transformer=None):
    val, source = self._get(name, default)
    if source and not source.supports_types:
      val = (transformer or typ)(val)
    if val is not None:
      assert isinstance(val, typ)
    return val

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

  def set_item(self, name, value):
    if self.sources:
      self.sources[0].set_item(name, value)
