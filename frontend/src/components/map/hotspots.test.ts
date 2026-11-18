import { describe, expect, it } from "vitest";
import { HOTSPOT_LEGEND, HOTSPOT_STEPS, hotspotStep } from "./hotspots";

describe("hotspotStep", () => {
  it("picks the band the score falls in", () => {
    expect(hotspotStep(0.5).label).toBe("Under 2");
    expect(hotspotStep(3).label).toBe("2 to 5");
    expect(hotspotStep(7).label).toBe("5 to 10");
    expect(hotspotStep(25).label).toBe("10 and above");
  });

  it("includes the lower bound of each band", () => {
    expect(hotspotStep(2).label).toBe("2 to 5");
    expect(hotspotStep(5).label).toBe("5 to 10");
    expect(hotspotStep(10).label).toBe("10 and above");
  });

  it("gives a bigger circle to a busier cell", () => {
    expect(hotspotStep(25).radius).toBeGreaterThan(hotspotStep(1).radius);
  });
});

describe("HOTSPOT_LEGEND", () => {
  it("has a row for each band", () => {
    expect(HOTSPOT_LEGEND).toHaveLength(HOTSPOT_STEPS.length);
  });
});
