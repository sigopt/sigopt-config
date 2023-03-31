# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigopt_config.source import MutableConfigBrokerSource, SecretConfigBrokerSource
from sigopt_config.vault_secrets.client import VaultClient


def create_vault_source(no_vault_broker, desired_secret_keys=None):
  vault_enabled = no_vault_broker.get("vault.enabled", False)
  if not vault_enabled:
    return None
  vault_client = VaultClient.from_config_broker(no_vault_broker)

  # NOTE: `desired_secret_keys` is the complete list of keys that we must be authorized to fetch from Vault.
  # If there is a desired secret stored in Vault that we cannot access, we must fail because it is unsafe
  # to proceed without it.
  #
  # We use `list_secrets` in order to see the secrets that are hosted in Vault, some of which we may not
  # have access to. If there are any that we desire but we don't have access to, we fail.
  # In addition, we block access to any keys that were not listed as `desired`, to prevent accidental use
  # of unspecified keys and enforce completeness of the `desrired_secret_keys` list.
  #
  #                               Block this secret,
  #                     -> No ->  whether or not it
  #   Do we desire the            is in Vault
  #   secret for this?
  #                                                -> No ->  FAIL
  #                     -> Yes -> Is the secret
  #                               stored in Vault?                              -> No ->  FAIL
  #                                                -> Yes -> Are we authorized
  #                                                          to see the secret?
  #                                                                             -> Yes -> Fetch secret from Vault
  all_hosted_keys = set(vault_client.list_secrets()["data"]["keys"])
  desired_secret_keys = set(desired_secret_keys) if desired_secret_keys is not None else all_hosted_keys
  blocked_keys = all_hosted_keys - desired_secret_keys

  config_data = MutableConfigBrokerSource()
  for key in desired_secret_keys:
    if not key.endswith("/"):
      response = vault_client.get_secret(key)
      for secret_key, secret_value in response["data"]["data"].items():
        config_data.set_item(f"{key}.{secret_key}", secret_value)

  for key in blocked_keys:
    config_data.set_not_available(key)
  return SecretConfigBrokerSource(config_data.underlying)
