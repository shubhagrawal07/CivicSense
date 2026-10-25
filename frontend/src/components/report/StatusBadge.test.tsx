import { describe, expect, it } from "vitest";
import { statusBadgeLabel } from "./StatusBadge";

describe("statusBadgeLabel", () => {
  it("shows an analysing/failed label before the issue status exists", () => {
    expect(statusBadgeLabel("PENDING")).toBe("Analysing");
    expect(statusBadgeLabel("PROCESSING")).toBe("Analysing");
    expect(statusBadgeLabel("FAILED")).toBe("Analysis failed");
  });

  it("shows the issue status once DONE, falling back to New", () => {
    expect(statusBadgeLabel("DONE", "NEW")).toBe("New");
    expect(statusBadgeLabel("DONE", "IN_PROGRESS")).toBe("In progress");
    expect(statusBadgeLabel("DONE", "RESOLVED")).toBe("Resolved");
    expect(statusBadgeLabel("DONE", null)).toBe("New");
  });
});
