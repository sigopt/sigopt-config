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

import ObjectSource from "./object";
import {coalesce, isDefinedAndNotNull, isJsObject} from "./utils";

const readYAMLFile = (filepath) => parseYAML(fs.readFileSync(filepath).toString());

class ConfigBroker {
  constructor(source) {
    this.source = source;
  }

  static fromConfigs(configs) {
    const reversed = [...configs];
    reversed.reverse();
    const data = _.reduce(reversed, jsonMergePatch.apply, {});
    return new ConfigBroker(new ObjectSource(data));
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

  get(key, defaultValue = undefined) {
    return this._ensureSafeReturn(this.source.get(key));
  }

  _ensureSafeReturn(value) {
    if (isJsObject(value)) {
      throw new Error(
        "Possibly unsafe .get of JSON object, values might be missing." +
          " Please use .getObject instead",
      );
    }
    return value;
  }

  getObject(key, defaultValue = undefined) {
    return this.source.get(key, defaultValue);
  }
}

export default ConfigBroker;
