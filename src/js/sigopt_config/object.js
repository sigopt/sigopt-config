/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

const dottedNameParts = (key) => key.split(".");

const getDottedNameFromObject = (object, key) => {
  const parts = dottedNameParts(key);
  const prefix = _.initial(parts);
  const suffix = _.last(parts);
  const parentObject = _.reduce(
    prefix,
    (memo, part) => {
      if (!memo) {
        return memo;
      }
      return memo[part];
    },
    object,
  );
  if (!parentObject) {
    return undefined;
  }
  return parentObject[suffix];
};

const setDottedNameFromObject = (object, key, value) => {
  const prefix = dottedNamePrefix(key);
  const suffix = dottedNameSuffix(key);
  const base = _.reduce(
    prefix,
    (memo, part) => {
      memo[part] = memo[part] || {};
      return memo[part];
    },
    object,
  );
  base[suffix] = value;
};

export default class ObjectSource {
  constructor(obj) {
    this.config = obj;
  }

  get(key) {
    return getDottedNameFromObject(this.config, key);
  }
}
