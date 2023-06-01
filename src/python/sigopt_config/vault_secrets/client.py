# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import os
import random
import time
from http import HTTPStatus

import requests
from sigopt_config.vault_secrets.login import AwsLogin, KubernetesLogin


AWS_AUTH_METHOD = "aws"
K8S_AUTH_METHOD = "k8s"


def retry_with_backoff(func):
  # pylint: disable=inconsistent-return-statements
  def wrapper(*args, **kwargs):
    NUM_RETRIES = 5
    for i in range(NUM_RETRIES + 1):
      try:
        return func(*args, **kwargs)
      except Exception as e:
        logging.getLogger("sigopt.vault").warning("encountered exception on try #%s: %s", (i + 1), e)
        time.sleep(2**i + random.random())  # nosec
        if i == NUM_RETRIES:
          raise e

  # pylint: enable=inconsistent-return-statements

  return wrapper


class VaultClient(object):
  @classmethod
  def from_config_broker(cls, config_broker):
    vault_config = config_broker.get_object("vault")
    auth_method = vault_config.get("auth_method", AWS_AUTH_METHOD)
    vault_client = cls(
      host=vault_config["host"],
      token=vault_config.get("token"),
      key_prefix=vault_config.get("key_prefix"),
      engine=vault_config.get("engine"),
    )
    login_method = {
      AWS_AUTH_METHOD: AwsLogin,
      K8S_AUTH_METHOD: KubernetesLogin,
    }[auth_method]()
    vault_client.login(login_method, vault_config)
    return vault_client

  def __init__(
    self,
    host,
    token=None,
    key_prefix=None,
    engine=None,
  ):
    self.host = host
    self.token = token or os.getenv("VAULT_TOKEN")
    self.key_prefix = key_prefix
    self.engine = engine or "secret"

  def login(self, login_method, vault_config):
    if self.token:
      logging.getLogger("sigopt.vault").warning("Token already set, skipping vault login")
      return
    auth_path = login_method.get_auth_path(vault_config)
    data = login_method.get_login_data(vault_config)
    fetch_token = self._fetch_token
    if login_method.should_retry:
      fetch_token = retry_with_backoff(fetch_token)
    self.token = fetch_token(auth_path, data)

  def _fetch_token(self, auth_path, payload):
    payload = {k: v for k, v in payload.items() if v}
    response = self._request("post", f"/v1/auth/{auth_path}/login", payload)
    return response["auth"]["client_token"]

  def _request(self, method, path, data=None):
    response = requests.request(
      method,
      self.host + path,
      data=json.dumps(data),
      headers={
        "X-Vault-Token": self.token,
      },
    )
    if response.status_code >= 400:
      raise requests.exceptions.HTTPError(f"path='{path}' :: " + response.text, response=response)
    assert response.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)
    if response.status_code == HTTPStatus.NO_CONTENT:
      return {}
    return response.json()

  def _secret_path(self, key, data_path="data"):
    parts = [part for part in (data_path, self.key_prefix, key) if part]
    path = "/".join(("v1", self.engine, *parts))
    return f"/{path}"

  def list_secrets(self, key=None):
    return self._request("list", self._secret_path(key, data_path="metadata"))

  def get_secret(self, key):
    return self._request("get", self._secret_path(key))

  def post_secret(self, key, data):
    return self._request("post", self._secret_path(key), data=data)
