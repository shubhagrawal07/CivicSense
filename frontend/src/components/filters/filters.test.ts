import { describe, expect, it } from "vitest";
import { EMPTY_FILTERS, toMapIssuesFilters } from "./filters";

describe("toMapIssuesFilters", () => {
  it("leaves out the filters that are not set", () => {
    expect(toMapIssuesFilters(EMPTY_FILTERS)).toEqual({
      category: undefined,
      severity: undefined,
      status: undefined,
      from: undefined,
      to: undefined,
    });
  });

  it("keeps the filters that are set", () => {
    const filters = toMapIssuesFilters({
      category: "pothole",
      severity: ["HIGH", "CRITICAL"],
      status: ["open"],
      from: "2026-01-01",
      to: "2026-01-31",
    });

    expect(filters).toEqual({
      category: "pothole",
      severity: ["HIGH", "CRITICAL"],
      status: ["open"],
      from: "2026-01-01",
      to: "2026-01-31",
    });
  });
});
