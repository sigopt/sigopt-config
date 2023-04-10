# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from sigopt_config.broker import *


class TestConfigBroker(object):
  def make_broker(self, configs):
    return ConfigBroker.from_configs(configs)

  def test_empty(self):
    broker = self.make_broker([])
    assert broker.get("fake.key", None) is None
    assert broker.get("fake.key", 1234) == 1234
    assert broker.get("fake.key", True) is True
    assert broker.get("fake.key", "abc") == "abc"

    assert broker.get("fake.key") is None
    with pytest.raises(KeyError):
      broker["fake.key"]

  def test_exists(self):
    dict1 = {
      "a": {
        "a1": 1,
        "a2": True,
        "a3": "aaa",
      },
      "c": {
        "conflict": True,
        "conflict_none": None,
      },
    }
    dict2 = {
      "b": {
        "b1": 3,
        "b2": False,
        "b3": "bbb",
      },
      "c": {
        "conflict": False,
        "conflict_none": 567,
      },
    }

    broker = ConfigBroker.from_configs([
      dict1,
      dict2,
    ])

    assert broker.get("a.a1", default=None) == 1
    assert broker.get("a.a2", default=None) is True
    assert broker.get("a.a3", default=None) == "aaa"
    assert broker.get("a.a4", default=None) is None
    assert broker.get("a.a4", default="xyz") == "xyz"
    with pytest.raises(KeyError):
      broker["a.a4"]

    assert broker.get("b.b1", default=None) == 3
    assert broker.get("b.b2", default=None) is False
    assert broker.get("b.b3", default=None) == "bbb"
    assert broker.get("b.b4", default="xyz") == "xyz"
    with pytest.raises(KeyError):
      broker["b.b4"]

    assert broker.get("c.conflict", default=None) is True
    assert broker.get("c.conflict_none") is None

    assert broker.get("d", default="xyz") == "xyz"

  def test_get_object(self):
    dict1 = {
      "a": {
        "a1": 1,
        "a2": True,
        "a3": "aaa",
      },
      "c": {
        "conflict": True,
        "conflict_none": None,
      },
    }
    dict2 = {
      "b": {
        "b1": 3,
        "b2": False,
        "b3": "bbb",
      },
      "c": {
        "conflict": False,
        "conflict_none": 567,
      },
    }

    broker = ConfigBroker.from_configs([
      dict1,
      dict2,
    ])

    assert broker.get("a") == {"a1": 1, "a2": True, "a3": "aaa"}
    assert broker.get("b") == {"b1": 3, "b2": False, "b3": "bbb"}
    assert broker.get("c") == {"conflict": True}
