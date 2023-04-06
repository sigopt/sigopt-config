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
import jmespath from "jmespath";

const readYAMLFile = (filepath) => parseYAML(fs.readFileSync(filepath).toString());

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
        files.sort();
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
    const value = jmespath.search(this.data, key);
    return typeof value === "undefined" ? defaultValue : value;
  }
}

export default ConfigBroker;
