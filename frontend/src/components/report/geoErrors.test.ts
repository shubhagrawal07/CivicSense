import { describe, expect, it } from "vitest";
import { geoErrorMessage } from "./geoErrors";

describe("geoErrorMessage", () => {
  it("explains how to unblock a denied permission", () => {
    expect(geoErrorMessage(1)).toContain("permission");
  });

  it("tells the user a timeout can be retried", () => {
    expect(geoErrorMessage(3)).toContain("too long");
  });

  it("gives a different message for each failure", () => {
    const messages = [1, 2, 3].map(geoErrorMessage);
    expect(new Set(messages).size).toBe(3);
  });

  it("falls back to a generic message for an unknown code", () => {
    expect(geoErrorMessage(99)).toContain("Could not access your location");
  });

  it("always suggests clicking the map", () => {
    for (const code of [1, 2, 3, 99]) {
      expect(geoErrorMessage(code)).toMatch(/click the map/i);
    }
  });
});
