/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import jmespath from "jmespath";
import jsonMergePatch from "json-merge-patch";
import path from "path";
import {parse as parseYAML} from "yaml";

const readYAMLFile = (filepath) =>
  parseYAML(fs.readFileSync(filepath).toString());

export class ConfigBroker {
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
        files.sort();
        let configs;
        try {
          configs = _.map(files, (file) => readYAMLFile(path.join(dir, file)));
        } catch (e) {
          return error(e);
        }
        return success(ConfigBroker.fromConfigs(configs));
      });
    });
  }

  constructor(data) {
    this.data = data;
  }

  get(key, defaultValue) {
    const value = jmespath.search(this.data, key);
    return typeof value === "undefined" ? defaultValue : value;
  }
}
