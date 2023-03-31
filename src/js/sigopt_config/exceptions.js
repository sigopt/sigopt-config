/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// NOTE: do we catch by class, and so need to use this base-class in sigopt-server?
export default class SigoptError extends Error {
  chain(causedBy) {
    this.stack += `\nCaused by: ${causedBy.stack}`;
    return this;
  }
}

export class HttpError extends SigoptError {
  constructor(options = {}) {
    super(options.message || "Unknown error");
    this.status = options.status;
    this.showNeedsLogin = options.showNeedsLogin || false;
    this.tokenStatus = options.tokenStatus || null;
  }

  isClientError() {
    return this.status && Math.floor(this.status / 100) === 4;
  }
}

export class ConfigBrokerValueNotAvailableException extends SigoptError {}
