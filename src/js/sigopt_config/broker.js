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

import EnvironmentSource from "./env";
import ObjectSource from "./object";
import VaultSource from "./vault";
import {coalesce, isDefinedAndNotNull, isJsObject} from "./utils";

const readYAMLFile = (filepath) => parseYAML(fs.readFileSync(filepath).toString());

class ConfigBroker {
  constructor(sources, vaultSecretKeys) {
    this._sources = sources;
    this._vaultSecretKeys = vaultSecretKeys;
  }

  static fromDirectory(dir, vaultSecretKeys) {
    return new Promise((success, error) => {
      fs.readdir(dir, (err, files) => {
        if (err) {
          return error(err);
        }
        const sources = _.map(files, (file) => readYAMLFile(path.join(dir, file)));
        const data = _.reduce(sources, jsonMergePatch.apply, {});
        const source = new ObjectSource(data);
        return success(new ConfigBroker([source, new EnvironmentSource()], vaultSecretKeys));
      });
    });
  }

  static fromFile(config, vaultSecretKeys) {
    const sources = [];
    let extend = config;
    while (isDefinedAndNotNull(extend)) {
      extend = path.resolve(extend);
      const data = readYAMLFile(extend);
      const original = extend;
      extend = data.extends;
      delete data.extends;
      sources.push(data);
      if (isDefinedAndNotNull(extend)) {
        let basedir = process.env.sigopt_api_config_dir || "./config";
        if (extend.startsWith("./") || extend.startsWith("../")) {
          basedir = path.dirname(original);
        }
        extend = path.join(basedir, extend);
      }
    }
    const data = _.reduce(sources, jsonMergePatch.apply, {});
    return new ConfigBroker([new ObjectSource(data), new EnvironmentSource()], vaultSecretKeys);
  }

  initialize(success, error) {
    const init = (sources) => {
      if (_.isEmpty(sources)) {
        return this._maybeAddVault(success, error);
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

  _maybeAddVault(success, error) {
    if (this.get("vault.enabled")) {
      const source = new VaultSource({
        engine: this.get("vault.engine"),
        host: this.get("vault.host"),
        keyPrefix: this.get("vault.key_prefix"),
        noncePath: this.get("vault.nonce_path"),
        // NOTE: vault.token is not specified in prod, but can be included for dev
        token: this.get("vault.token"),
        vaultSecretKeys: this._vaultSecretKeys,
      });
      this._sources.push(source);
      return source.initialize(success, error);
    } else {
      return success();
    }
  }

  allConfigsForLogging() {
    return _.map(this._sources, (source) => source.allConfigsForLogging());
  }
}

export default ConfigBroker;
