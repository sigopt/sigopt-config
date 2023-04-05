import os

import pytest
import yaml

from sigopt_config.broker import ConfigBroker

cases_root_path = os.path.join(".", "test", "cases")
supported_methods = ["get", "get_object"]

def generate_test_cases():
  case_names = os.listdir(cases_root_path)
  assert case_names
  cases = []
  for case_name in case_names:
    case_path = os.path.join(cases_root_path, case_name)
    ls = set(os.listdir(case_path))
    ls.remove("config")
    ls.remove("test.yaml")
    assert not ls, f"Extra files found in test case {case_name}: {ls}"
    with open(os.path.join(case_path, "test.yaml")) as test_config_fp:
      test_config = yaml.safe_load(test_config_fp)
    for method in supported_methods:
      method_cases = test_config.pop(method, None)
      if method_cases is None:
        continue
      assert isinstance(method_cases, list)
      for method_case in method_cases:
        assert isinstance(method_case, dict)
        key = method_case.pop("key")
        assert isinstance(key, str)
        expected = method_case.pop("expected")
        cases.append([case_name, method, key, expected])
    assert not test_config, f"Unused tests in {case_name}: {test_config}"
  return cases

class ConfigTest:
  @pytest.mark.parametrize("case_name,method,key,expected", generate_test_cases())
  def test_load_config(self, case_name, method, key, expected):
    config_dir = os.path.join(cases_root_path, case_name, "config")
    result = self.load_config_value(config_dir, method, key)
    assert result == expected

class TestConfigBroker(ConfigTest):
  def load_broker(self, config_dir):
    return ConfigBroker.from_directory(config_dir, include_vault=False)

  def load_config_value(self, config_dir, method, key):
    broker = self.load_broker(config_dir)
    return getattr(broker, method)(key)
