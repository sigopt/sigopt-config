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
  def __init__(self, d):
    self.d = d

  def _split_name(self, name):
    return name.split(".")

  def __contains__(self, name):
    return self._do_get(name, default=None)[0]

  def get(self, name, default=None):
    return self._do_get(name, default)[1]

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


class ConfigBrokerValueNotAvailableException(KeyError):
  pass
