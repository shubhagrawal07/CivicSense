import { describe, expect, it } from "vitest";
import { buildWardRanges, wardColour } from "./wardColours";

describe("ward colours", () => {
  it("splits the highest count into 5 ranges and colours a count by its range", () => {
    const ranges = buildWardRanges(34);

    expect(ranges.map((r) => [r.min, r.max])).toEqual([
      [0, 7],
      [8, 14],
      [15, 21],
      [22, 28],
      [29, 35],
    ]);
    expect(wardColour(0, ranges)).toBe(ranges[0].colour);
    expect(wardColour(8, ranges)).toBe(ranges[1].colour);
    expect(wardColour(34, ranges)).toBe(ranges[4].colour);
  });
});
