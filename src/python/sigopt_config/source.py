# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

from sigopt_config.utils import is_mapping


class _NotAvailableClass(object):
  def __repr__(self):
    return "NotAvailable"


_NOT_AVAILABLE = _NotAvailableClass()


class ConfigBrokerSource(object):
  supports_types = True

  def _split_name(self, name):
    return name.split(".")

  def __contains__(self, name):
    raise NotImplementedError()

  def get(self, name, default=None):
    raise NotImplementedError()

  def all_configs_for_logging(self):
    raise NotImplementedError()


class DecoratorConfigBrokerSource(ConfigBrokerSource):
  def __init__(self, underlying):
    super().__init__()
    self.underlying = underlying

  def __contains__(self, name):
    return self.underlying.__contains__(name)

  def get(self, name, default=None):
    return self.underlying.get(name, default=default)

  def all_configs_for_logging(self):
    return self.underlying.all_configs_for_logging()


class MutableConfigBrokerSource(DecoratorConfigBrokerSource):
  def __init__(self):
    data = {}
    super().__init__(DictConfigBrokerSource(data))
    self._dict = data

  def set_item(self, name, value):
    parts = self._split_name(name)
    base_dict = self._dict
    for p in parts[:-1]:
      base_dict = base_dict.setdefault(p, {})
      if not is_mapping(base_dict):
        raise Exception(f"Expected object for key {p} in {name} - found {type(base_dict)}")
    base_dict[parts[-1]] = value

  def set_not_available(self, name):
    self.set_item(name, _NOT_AVAILABLE)

  def reset(self):
    self._dict.clear()


class SecretConfigBrokerSource(DecoratorConfigBrokerSource):
  supports_types = True

  def all_configs_for_logging(self):
    return {k: "*****" for k in self.underlying.all_configs_for_logging()}


class EnvironmentConfigBrokerSource(DecoratorConfigBrokerSource):
  supports_types = False
  PREFIX = "sigopt."

  def __init__(self):
    super().__init__(MutableConfigBrokerSource())
    for k, v in os.environ.items():
      if k.startswith(self.PREFIX):
        k = k[len(self.PREFIX) :]
        self.underlying.set_item(k, v)


class ConfigBrokerValueNotAvailableException(KeyError):
  pass


class DictConfigBrokerSource(ConfigBrokerSource):
  supports_types = True

  def __init__(self, d):
    super().__init__()
    self.d = d

  def __contains__(self, name):
    return self._do_get(name, default=None)[0]

  def get(self, name, default=None):
    return self._do_get(name, default)[1]

  def all_configs_for_logging(self):
    return self._remove_unavailable(self.d)

  def _remove_unavailable(self, value):
    if is_mapping(value):
      return {k: "_NOT_AVAILABLE" if v is _NOT_AVAILABLE else self._remove_unavailable(v) for k, v in value.items()}
    return value

  def _do_get(self, name, default):
    # Returns a tuple (did_contain, value), so we can distinguish between
    # null being explicitly present or not

    base_dict = self.d
    parts = self._split_name(name)

    for p in parts[:-1]:
      base_dict = base_dict.get(p)
      if base_dict is _NOT_AVAILABLE:
        raise ConfigBrokerValueNotAvailableException()
      if not is_mapping(base_dict):
        return (False, None)

    if is_mapping(base_dict):
      did_contain = parts[-1] in base_dict
      value = base_dict.get(parts[-1], default)
      self._raise_on_not_available(value)
      return (did_contain, value)
    else:
      return (False, None)

  def _raise_on_not_available(self, value):
    if value is _NOT_AVAILABLE:
      raise ConfigBrokerValueNotAvailableException()
    if is_mapping(value):
      for v in value.values():
        self._raise_on_not_available(v)
