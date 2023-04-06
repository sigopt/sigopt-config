/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import path from "path";
import {parse as parseYAML} from "yaml";
import jsonMergePatch from "json-merge-patch";

const readYAMLFile = (filepath) => parseYAML(fs.readFileSync(filepath).toString());

const dottedNameParts = (key) => key.split(".");

const getDottedNameFromObject = (object, key) => {
  const parts = dottedNameParts(key);
  const prefix = _.initial(parts);
  const suffix = _.last(parts);
  const parentObject = _.reduce(
    prefix,
    (memo, part) => {
      if (!_.isObject(memo)) {
        return memo;
      }
      return memo[part];
    },
    object,
  );
  if (typeof parentObject === "undefined") {
    return undefined;
  }
  return parentObject[suffix];
};

class ConfigBroker {
  static fromConfigs(configs) {
    const reversed = [...configs];
    reversed.reverse();
    const data = _.reduce(reversed, jsonMergePatch.apply, {});
    return new ConfigBroker(data);
  }

  static fromDirectory(dir) {
    return new Promise((success, error) => {
      fs.readdir(dir, (err, files) => {
        if (err) {
          return error(err);
        }
        let configs;
        try {
          configs = _.map(files, (file) => readYAMLFile(path.join(dir, file)));
        } catch (err) {
          return error(err);
        }
        return success(ConfigBroker.fromConfigs(configs));
      });
    });
  }

  constructor(data) {
    this.data = data;
  }

  get(key, defaultValue) {
    const value = getDottedNameFromObject(this.data, key);
    return typeof value === "undefined" ? defaultValue : value;
  }
}

export default ConfigBroker;
