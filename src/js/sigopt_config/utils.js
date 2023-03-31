/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export const isJsObject = (obj) =>
  _.isObject(obj) && !_.isFunction(obj) && !_.isArray(obj);

export const isUndefinedOrNull = (arg) => arg === undefined || arg === null;

export const isDefinedAndNotNull = (arg) => !isUndefinedOrNull(arg);

// Returns the first non-undefined and non-null argument.
// Returns undefined if there are no such arguments.
export const coalesce = (...args) =>
  _.find(args, (a) => isDefinedAndNotNull(a));

export const startsWith = (baseString, searchString) =>
  baseString.indexOf(searchString) === 0;

export const compactObject = (obj) => _.omit(obj, _.isEmpty);
