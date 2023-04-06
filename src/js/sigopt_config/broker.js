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

  static fromDirectory(dir) {
    return new Promise((success, error) => {
      fs.readdir(dir, (err, files) => {
        if (err) {
          return error(err);
        }
        try {
          const configs = _.map(files, (file) => readYAMLFile(path.join(dir, file)));
        } catch (err) {
          return error(err);
        }
        const data = _.reduce(configs, jsonMergePatch.apply, {});
        const source = new ObjectSource(data);
        return success(new ConfigBroker(source));
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
