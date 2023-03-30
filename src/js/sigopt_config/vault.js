import _ from "underscore";
import fs from "fs";
// eslint-disable-next-line import/no-unresolved
import got from "got";
import os from "os";
import promisify from "es6-promisify";

import ObjectSource from "./object";
import {SigoptError, HttpError} from "./exceptions";
import {compactObject} from "./utils";
import {AWS_METADATA_URL} from "./constants";


export default class VaultSource {
  constructor(options) {
    this._nonce_path = options.noncePath;
    this._certificate = null;
    this._engine = options.engine || "secret";
    this._host = options.host;
    this._keyPrefix = options.keyPrefix;
    this._token = options.token;
    this._underlying = null;
    this._vaultSecretKeys = options.vaultSecretKeys;
  }

  initialize(success, error) {
    (this._token ? Promise.resolve(this._token) : this._initializeToken())
      .then(() => this._populateCache())
      .then((cache) => {
        this._underlying = cache;
      })
      .then(() => new Promise((s, e) => this._underlying.initialize(s, e)))
      .then(success, error);
  }

  _initializeToken() {
    return Promise.all([
      this._fetchNonce(),
      this._fetchPkcs7(),
      this._fetchRole(),
    ]).then(([nonce, pkcs7, role]) =>
      this._request(
        "post",
        "/v1/auth/aws/login",
        compactObject({nonce, pkcs7, role}),
      ).then((body) => {
        this._token = body.auth.client_token;
        return this._persistNonce(nonce);
      }),
    );
  }

  _fetchPkcs7() {
    return this._fetchRequestBody(
      `${AWS_METADATA_URL}/dynamic/instance-identity/pkcs7`,
    ).then((pkcs7) => pkcs7.replace(/\n/gu, ""));
  }

  _fetchRole() {
    return this._fetchRequestBody(
      `${AWS_METADATA_URL}/meta-data/iam/security-credentials/`,
    );
  }

  _fetchNonce() {
    return promisify(
      fs.readFile,
      fs,
    )(this.nonce_path)
      .then((data) => data.toString("utf8"))
      .catch((err) =>
        err.code === "ENOENT" ? Promise.resolve(null) : Promise.reject(err),
      );
  }

  _persistNonce(nonce) {
    const cleanup = promisify(fs.close, fs);
    return promisify(fs.open, fs)(this.nonce_path, "wx", 0o600)
      .then((fd) =>
        promisify(fs.write, fs)(fd, nonce).then(
          () => cleanup(fd),
          (err) => cleanup(fd).then(() => Promise.reject(err)),
        ),
      )
      .catch((err) =>
        err.code === "EEXIST" ? Promise.resolve(null) : Promise.reject(err),
      );
  }

  get(key) {
    return this._underlying.get(key);
  }

  _secretPath(key, dataPath = "data") {
    const path = (k) => (this._keyPrefix ? `${this._keyPrefix}/${k}` : k);
    return `/v1/${this._engine}/${dataPath}/${path(key)}`;
  }

  _populateCache() {
    return this._request("list", this._secretPath("", "metadata"))
      .then((response) => _.reject(response.data.keys, (k) => k.endsWith("/")))
      .then((keys) => {
        const blockedKeys = _.difference(keys, this._vaultSecretKeys);
        const fetchPromises = _.map(this._vaultSecretKeys, (key) =>
          this._request("get", this._secretPath(key))
            .then((response) => response.data.data)
            .then((data) => [key, data]),
        );
        return Promise.all(fetchPromises)
          .then(_.object)
          .then((cacheData) => {
            const source = new ObjectSource(cacheData);
            _.each(blockedKeys, (key) => source.setNotAvailable(key));
            return source;
          });
      });
  }

  _fetchRequestBody(...args) {
    const chain = new SigoptError();
    return got(...args).then((response) =>
      response.statusCode === 200
        ? Promise.resolve(response.body)
        : Promise.reject(
            new HttpError({
              message: response.body,
              status: response.statusCode,
            }).chain(chain),
          ),
    );
  }

  _request(method, path, data) {
    return this._fetchRequestBody(this._host + path, {
      json: data,
      headers: compactObject({"X-Vault-Token": this._token}),
      method: method,
      responseType: "json",
    });
  }

  allConfigsForLogging() {
    return _.mapObject(this._underlying.allConfigsForLogging(), () => "***");
  }
}
