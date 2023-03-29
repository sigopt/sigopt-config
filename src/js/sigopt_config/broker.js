import _ from "underscore";
import fs from "fs";
import path from "path";

import EnvironmentSource from "./env";
import ObjectSource from "./object";
import VaultSource from "./vault";
import {coalesce, isDefinedAndNotNull, isJsObject} from "./utils";

class ConfigBroker {
  constructor(sources) {
    this._sources = sources;
  }

  static fromFile(config) {
    const sources = [];
    let extend = config;
    while (isDefinedAndNotNull(extend)) {
      extend = path.resolve(extend);
      const data = JSON.parse(fs.readFileSync(extend));
      const original = extend;
      extend = data.extends;
      delete data.extends;
      sources.push(new ObjectSource(data));
      if (isDefinedAndNotNull(extend)) {
        let basedir = process.env.sigopt_api_config_dir || "./config";
        if (extend.startsWith("./") || extend.startsWith("../")) {
          basedir = path.dirname(original);
        }
        extend = path.join(basedir, extend);
      }
    }
    sources.push(new EnvironmentSource());
    return new ConfigBroker(sources);
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
        // NOTE(patrick): vault.token is not specified in prod, but can be included for dev
        // You can get the root vault token from 1password, but be very careful with it since it has all privileges
        token: this.get("vault.token"),
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
