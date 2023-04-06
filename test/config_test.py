import json
import os
import subprocess

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

class TestPythonConfigBroker(ConfigTest):
  def load_broker(self, config_dir):
    return ConfigBroker.from_directory(config_dir)

  def load_config_value(self, config_dir, method, key):
    broker = self.load_broker(config_dir)
    return getattr(broker, method)(key)

class TestJsConfigBroker(ConfigTest):
  broker_proc = None

  @pytest.fixture(autouse=True, scope="session")
  @classmethod
  def start_broker_proc(cls):
    cls.broker_proc = subprocess.Popen(
        ["npx", "babel-node", "test/js_config_loader.js"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    yield
    cls.exec_command("done")
    cls.broker_proc.wait()
    cls.broker_proc = None

  @classmethod
  def exec_command(cls, command, **kwargs):
    cls.broker_proc.stdin.writelines([
      (json.dumps({"command": command, **kwargs}) + "\n").encode(),
    ])
    cls.broker_proc.stdin.flush()
    response = cls.broker_proc.stdout.readline()
    response = json.loads(response)
    assert "error" not in response, response["error"]
    return response

  def load_config_value(self, config_dir, method, key):
    self.exec_command("load", directory=config_dir)
    try:
      value = self.exec_command("read", method=method, key=key)["value"]
    finally:
      self.exec_command("reset")
    return value