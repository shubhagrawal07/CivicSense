import { describe, expect, it } from "vitest";
import { SEVERITY_COLORS, SEVERITY_LEGEND, UNCLASSIFIED_COLOR, severityColor } from "./severity";

describe("severityColor", () => {
  it("returns the colour for each severity", () => {
    expect(severityColor("CRITICAL")).toBe(SEVERITY_COLORS.CRITICAL);
    expect(severityColor("HIGH")).toBe(SEVERITY_COLORS.HIGH);
    expect(severityColor("MEDIUM")).toBe(SEVERITY_COLORS.MEDIUM);
    expect(severityColor("LOW")).toBe(SEVERITY_COLORS.LOW);
  });

  it("returns the unclassified colour when severity is null", () => {
    expect(severityColor(null)).toBe(UNCLASSIFIED_COLOR);
  });
});

describe("SEVERITY_LEGEND", () => {
  it("has a row for each severity plus unclassified", () => {
    expect(SEVERITY_LEGEND).toHaveLength(5);
  });

  it("uses the same colours as severityColor", () => {
    const colors = SEVERITY_LEGEND.map((entry) => entry.color);
    expect(colors).toEqual([
      severityColor("CRITICAL"),
      severityColor("HIGH"),
      severityColor("MEDIUM"),
      severityColor("LOW"),
      severityColor(null),
    ]);
  });
});
