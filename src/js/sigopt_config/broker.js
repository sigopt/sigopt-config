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
  constructor(sources) {
    this._sources = sources;
  }

  static fromDirectory(dir) {
    return new Promise((success, error) => {
      fs.readdir(dir, (err, files) => {
        if (err) {
          return error(err);
        }
        const sources = _.map(files, (file) => readYAMLFile(path.join(dir, file)));
        const data = _.reduce(sources, jsonMergePatch.apply, {});
        const source = new ObjectSource(data);
        return success(new ConfigBroker([source]));
      });
    });
  }

  initialize(success, error) {
    const init = (sources) => {
      if (_.isEmpty(sources)) {
        return success();
      } else {
        return sources[0].initialize(_.partial(init, sources.slice(1)), error);
      }
    };
    init(this._sources);
  }

  get(key, defaultValue = undefined) {
    return this._ensureSafeReturn(
      coalesce(
        _.reduce(
          this._sources,
          (memo, source) => (memo === undefined ? source.get(key) : memo),
          undefined,
        ),
        defaultValue,
      ),
    );
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
    const values = _.without(
      _.map(this._sources, (source) => source.get(key)),
      undefined,
    );
    values.reverse();
    return _.isEmpty(values) ? defaultValue : _.extend({}, ...values);
  }
}

export default ConfigBroker;
