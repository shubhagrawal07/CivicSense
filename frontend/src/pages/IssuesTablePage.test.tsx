import { describe, expect, it } from "vitest";
import { buildFilterQuery, sortFeatures } from "./IssuesTablePage";
import type { MapFeature } from "../api/types";

function feature(
  id: number,
  category: string,
  reportCount: number,
  lastReportedAt: string,
): MapFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [72.9, 19.1] },
    properties: {
      id,
      category,
      severity: "MEDIUM",
      status: "NEW",
      report_count: reportCount,
      last_reported_at: lastReportedAt,
    },
  };
}

describe("sortFeatures", () => {
  it("sorts ascending by the given key", () => {
    const features = [
      feature(2, "garbage", 3, "2026-01-02"),
      feature(1, "pothole", 1, "2026-01-01"),
    ];

    const sorted = sortFeatures(features, { key: "id", direction: "asc" });

    expect(sorted.map((f) => f.properties.id)).toEqual([1, 2]);
  });

  it("sorts descending by the given key", () => {
    const features = [
      feature(1, "pothole", 1, "2026-01-01"),
      feature(2, "garbage", 3, "2026-01-02"),
    ];

    const sorted = sortFeatures(features, {
      key: "report_count",
      direction: "desc",
    });

    expect(sorted.map((f) => f.properties.id)).toEqual([2, 1]);
  });
});

describe("buildFilterQuery", () => {
  it("includes only the filters that are set", () => {
    const query = buildFilterQuery({
      category: "pothole",
      severity: [],
      status: [],
      from: "",
      to: "",
    });

    expect(query).toBe("category=pothole");
  });

  it("repeats the key for each value in an array filter", () => {
    const query = buildFilterQuery({
      category: "",
      severity: ["HIGH", "CRITICAL"],
      status: ["open"],
      from: "2026-01-01",
      to: "2026-01-31",
    });

    expect(query).toBe(
      "severity=HIGH&severity=CRITICAL&status=open&from=2026-01-01&to=2026-01-31",
    );
  });
});
