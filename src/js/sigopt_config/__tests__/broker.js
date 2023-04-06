/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ConfigBroker from "../broker";

const source1 = {a: {b: "c", d: "e"}};
const source2 = {a: {b: "f", y: "z"}};

describe("ConfigBroker", () => {
  it("fetches from multiple sources", () => {
    const broker = ConfigBroker.fromConfigs([source1, source2]);
    expect(broker.get("a.b")).toEqual("c");
    expect(broker.get("a.d")).toEqual("e");
    expect(broker.get("a.y")).toEqual("z");
    expect(broker.getObject("a")).toEqual({
      b: "c",
      d: "e",
      y: "z",
    });
  });
});
