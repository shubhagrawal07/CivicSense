import { describe, expect, it } from "vitest";
import { toReport } from "./reports";
import type { ReportDetailResponse } from "./types";

const done: ReportDetailResponse = {
  id: 12,
  description: "Big pothole near the gate",
  image_url: "/uploads/photo.jpg",
  location: { lat: 19.13, lng: 72.91 },
  created_at: "2026-11-12T10:00:00Z",
  processing_status: "DONE",
  error: null,
  classification: { category: "pothole", source: "BOTH", conflict: false },
  department: { id: 1, name: "Roads and Infrastructure" },
  severity: { level: "HIGH" },
  issue: { id: 7 },
};

const pending: ReportDetailResponse = {
  id: 13,
  description: null,
  image_url: null,
  location: { lat: 19.13, lng: 72.91 },
  created_at: "2026-11-12T10:05:00Z",
  processing_status: "PENDING",
  error: null,
  classification: null,
  department: null,
  severity: null,
  issue: null,
};

describe("toReport", () => {
  it("flattens a finished report", () => {
    const report = toReport(done);

    expect(report.id).toBe("12");
    expect(report.latitude).toBe(19.13);
    expect(report.longitude).toBe(72.91);
    expect(report.image_path).toBe("/uploads/photo.jpg");
    expect(report.classification).toBe("pothole");
    expect(report.classification_source).toBe("BOTH");
    expect(report.conflict).toBe(false);
    expect(report.department).toEqual({
      id: 1,
      name: "Roads and Infrastructure",
    });
    expect(report.predicted_severity).toBe("HIGH");
    expect(report.issue).toEqual({ id: 7 });
  });

  it("leaves the analysis fields empty while the report is still pending", () => {
    const report = toReport(pending);

    expect(report.id).toBe("13");
    expect(report.classification).toBeNull();
    expect(report.classification_source).toBeNull();
    expect(report.conflict).toBe(false);
    expect(report.department).toBeNull();
    expect(report.predicted_severity).toBeNull();
    expect(report.issue).toBeNull();
    expect(report.latitude).toBe(19.13);
  });
});
