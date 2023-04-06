import json
import os
import subprocess

import pytest
import yaml

from sigopt_config.broker import ConfigBroker

cases_root_path = os.path.join(".", "test", "cases")

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
    assert isinstance(test_config, list)
    for case in test_config:
      assert isinstance(case, dict)
      key = case.pop("key")
      assert isinstance(key, str)
      expected = case.pop("expected")
      assert not case, f"Extra arguments found in test case {case_name}: {case}"
      cases.append([case_name, key, expected])
  return cases

class ConfigTest:
  @pytest.mark.parametrize("case_name,key,expected", generate_test_cases())
  def test_load_config(self, case_name, key, expected):
    config_dir = os.path.join(cases_root_path, case_name, "config")
    result = self.load_config_value(config_dir, key)
    assert result == expected

class TestPythonConfigBroker(ConfigTest):
  def load_broker(self, config_dir):
    return ConfigBroker.from_directory(config_dir)

  def load_config_value(self, config_dir, key):
    broker = self.load_broker(config_dir)
    return broker.get(key)

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

  def load_config_value(self, config_dir, key):
    self.exec_command("load", directory=config_dir)
    try:
      value = self.exec_command("get", key=key).get("value")
    finally:
      self.exec_command("reset")
    return value
