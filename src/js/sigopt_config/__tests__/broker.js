/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ConfigBroker from "../broker";
import ObjectSource from "../object";
import {ConfigBrokerValueNotAvailableException} from "../exceptions";

const source1 = new ObjectSource({a: {b: "c", d: "e"}});
const source2 = new ObjectSource({a: {b: "f", y: "z"}});

describe("ConfigBroker", () => {
  it("fetches from multiple sources", (done) => {
    const broker = new ConfigBroker([source1, source2]);
    broker.initialize(() => {
      expect(broker.get("a.b")).toEqual("c");
      expect(broker.get("a.d")).toEqual("e");
      expect(broker.get("a.y")).toEqual("z");
      expect(() => broker.getObject("not")).toThrow(
        ConfigBrokerValueNotAvailableException,
      );
      expect(broker.getObject("a")).toEqual({
        b: "c",
        d: "e",
        y: "z",
      });
      done();
    }, done.fail);
  });
});
