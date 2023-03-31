# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

import requests


# NOTE: may not live here long term
AWS_METADATA_URL = "http://169.254.169.254/latest"


class VaultLogin(object):
  should_retry = False

  def get_auth_path(self, vault_config):
    raise NotImplementedError()

  def get_login_data(self, vault_config):
    raise NotImplementedError()


class AwsLogin(VaultLogin):
  # NOTE: This login method requires that the IAM role for the instance has been granted access to vault.
  # Full documentation is available here: https://www.vaultproject.io/docs/auth/aws/

  should_retry = True

  def get_auth_path(self, vault_config):
    return "aws"

  def get_login_data(self, vault_config):
    nonce_path = vault_config["nonce_path"]
    nonce = self._get_nonce(nonce_path)
    pkcs7 = self._get_pkcs7()
    role = self._get_role()
    return {
      "role": role,
      "nonce": nonce,
      "pkcs7": pkcs7,
    }

  def _get_nonce(self):
    # NOTE: As an added security measure, Vault will accept a unique nonce value when you
    # first login to the instance. This is to prevent replay attacks where someone else can just
    # log in with the same credentials, as subsequent login attempts must reuse the nonce. However,
    # if the nonce is lost, you may not be able to log in from that instance again. To recover from
    # this state, you may need to delete the instance from the identity-accesslist in vault
    return self._fetch_nonce()

  def _fetch_nonce(self, nonce_path):
    if os.path.exists(nonce_path):
      with open(nonce_path, "r") as f:
        nonce = f.read().strip()
        assert nonce
        return nonce
    return None

  def _get_role(self):
    return self._get_from_aws_metadata("/meta-data/iam/security-credentials/")

  def _get_pkcs7(self):
    return self._get_from_aws_metadata("/dynamic/instance-identity/pkcs7").replace("\n", "")

  def _get_from_aws_metadata(self, path):
    try:
      r = requests.get(f"{AWS_METADATA_URL}{path}", timeout=1)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
      raise Exception(
        f"Couldn't fetch AWS metadata from {AWS_METADATA_URL}."
        " Are you running on an AWS machine?"
        " If not, you must provide an explicit token via the vault.token config to use vault."
      ) from e
    r.raise_for_status()
    return r.text.replace("\n", "")


class KubernetesLogin(VaultLogin):
  # NOTE: This login method requires that the provided role exists at auth/kubernetes/role/{role}.
  # Full documentation is available here: https://www.vaultproject.io/docs/auth/kubernetes/
  # Example: https://learn.hashicorp.com/vault/identity-access-management/vault-agent-k8s

  SA_JWT_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"

  def get_auth_path(self, vault_config):
    return vault_config.get("auth_path", "kubernetes")

  def get_login_data(self, vault_config):
    role = vault_config.get("role")
    if role is None:
      raise Exception("Must provide a role to initialize the vault token in kubernetes")
    with open(self.SA_JWT_PATH) as jwt_fp:
      jwt = jwt_fp.read()
    return {
      "role": role,
      "jwt": jwt,
    }
