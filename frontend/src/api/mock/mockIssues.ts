import { mockGetReport } from "./mockReports";
import type { Issue } from "../types";

const potholeIssue: Issue = {
  id: 1,
  category: "pothole",
  severity: "HIGH",
  status: "IN_PROGRESS",
  location: { lat: 19.1334, lng: 72.9133 },
  report_count: 4,
  first_reported_at: "2026-10-02T09:15:00Z",
  last_reported_at: "2026-10-09T17:40:00Z",
  department: { id: 1, name: "Roads and Infrastructure" },
  authority: { id: 1, name: "Municipal Corporation", jurisdiction: "Mumbai" },
  contacts: [
    {
      type: "HELPLINE",
      value: "1916",
      source_url: "https://portal.mcgm.gov.in/",
      last_verified_at: "2026-09-20",
      verified: true,
    },
    {
      type: "EMAIL",
      value: "complaints@example.org",
      source_url: null,
      last_verified_at: null,
      verified: false,
    },
  ],
  status_history: [
    { status: "NEW", changed_at: "2026-10-02T09:15:00Z", note: null },
    {
      status: "ASSIGNED",
      changed_at: "2026-10-04T11:00:00Z",
      note: "Assigned to the ward office",
    },
    { status: "IN_PROGRESS", changed_at: "2026-10-08T08:30:00Z", note: null },
  ],
};

export async function mockGetIssue(id: string): Promise<Issue> {
  if (id === String(potholeIssue.id)) return potholeIssue;

  const report = await mockGetReport(id);
  if (report.processing_status !== "DONE") {
    const error = new Error(`Issue ${id} not found`);
    (error as Error & { status?: number }).status = 404;
    throw error;
  }

  return {
    id: Number(id),
    category: report.classification ?? "other",
    severity: report.predicted_severity ?? null,
    status: "NEW",
    location: { lat: report.latitude, lng: report.longitude },
    report_count: 1,
    first_reported_at: report.created_at,
    last_reported_at: report.created_at,
    department: null,
    authority: null,
    contacts: [],
    status_history: [
      { status: "NEW", changed_at: report.created_at, note: null },
    ],
  };
}
