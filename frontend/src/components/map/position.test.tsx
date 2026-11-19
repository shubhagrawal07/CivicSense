import { describe, expect, it } from "vitest";
import { featurePosition } from "./position";
import type { MapFeature } from "../../api/types";

function feature(coordinates: [number, number]): MapFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates },
    properties: {
      id: 1,
      category: "pothole",
      severity: "HIGH",
      status: "NEW",
      report_count: 2,
      last_reported_at: "2026-11-01T10:00:00Z",
    },
  };
}

describe("featurePosition", () => {
  it("reverses GeoJSON lng/lat order for leaflet", () => {
    expect(featurePosition(feature([72.8777, 19.076]))).toEqual([19.076, 72.8777]);
  });
});
