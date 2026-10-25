import type {
  MyReportListItem,
  MyReportsResponse,
  ProcessingStatus,
  Report,
  SubmitReportPayload,
  SubmitReportResponse,
} from "../types";

// In-memory mock of the report submission + background-processing flow,
// used while SL-11 (backend report API) and SL-16 (processing pipeline) are
// not yet available. A report transitions PENDING -> PROCESSING -> DONE on
// its own after a short delay, so the polling UI has something real to react
// to. Delete this module (and the VITE_USE_MOCK_API switch in reports.ts)
// once the real backend is wired up.

const MOCK_DELAY_PROCESSING_MS = 1500;
const MOCK_DELAY_DONE_MS = 6000;

const reports = new Map<string, Report>();
let nextId = 1;

function demoReport(
  description: string,
  status: ProcessingStatus,
  hoursAgo: number,
): Report {
  return {
    id: String(nextId++),
    description: description,
    image_path: null,
    latitude: 0,
    longitude: 0,
    processing_status: status,
    created_at: new Date(Date.now() - hoursAgo * 60 * 60 * 1000).toISOString(),
  };
}

const demoReports: Report[] = [
  {
    ...demoReport("Large pothole on Main St", "DONE", 5),
    classification: "pothole",
    predicted_severity: "HIGH",
  },
  {
    ...demoReport("Streetlight out near the park", "DONE", 4),
    classification: "lighting",
    predicted_severity: "LOW",
  },
  demoReport("Overflowing bin on 5th Ave", "PENDING", 3),
  demoReport("Graffiti on the underpass wall", "PROCESSING", 2),
  {
    ...demoReport("Broken fence near the school", "FAILED", 1),
    error: "Mock processing failed.",
  },
];

for (const report of demoReports) {
  reports.set(report.id, report);
}

function toListItem(report: Report): MyReportListItem {
  const item: MyReportListItem = {
    id: report.id,
    description_preview: report.description?.slice(0, 80),
    thumbnail_url: report.image_path,
    created_at: report.created_at,
    processing_status: report.processing_status,
  };

  if (report.processing_status !== "DONE") {
    return item;
  }

  return {
    ...item,
    category: report.classification,
    severity_level: report.predicted_severity,
    issue_id: report.id,
    issue_status: "NEW",
    report_count: 1,
  };
}

// Submitting a description containing the word "fail" (case-insensitive)
// produces a FAILED report, for exercising the error UI without waiting.
function willFail(payload: SubmitReportPayload): boolean {
  return (payload.description ?? "").toLowerCase().includes("fail");
}

export async function mockSubmitReport(
  payload: SubmitReportPayload,
): Promise<SubmitReportResponse> {
  if (!payload.description && !payload.image) {
    throw mockValidationError();
  }

  const id = String(nextId++);
  const createdAt = new Date().toISOString();

  const report: Report = {
    id,
    description: payload.description ?? null,
    image_path: payload.image ? payload.image.name : null,
    latitude: payload.latitude,
    longitude: payload.longitude,
    processing_status: "PENDING",
    created_at: createdAt,
  };
  reports.set(id, report);

  setTimeout(() => {
    const current = reports.get(id);
    if (!current) return;
    reports.set(id, { ...current, processing_status: "PROCESSING" });
  }, MOCK_DELAY_PROCESSING_MS);

  setTimeout(() => {
    const current = reports.get(id);
    if (!current) return;

    if (willFail(payload)) {
      reports.set(id, {
        ...current,
        processing_status: "FAILED",
        error: "Mock failure: description contained \"fail\".",
        processed_at: new Date().toISOString(),
      });
      return;
    }

    reports.set(id, {
      ...current,
      processing_status: "DONE",
      classification: "pothole",
      classification_confidence: 0.87,
      classification_source: payload.image
        ? payload.description
          ? "BOTH"
          : "IMAGE"
        : "TEXT",
      conflict: false,
      needs_review: false,
      predicted_department_id: 1,
      department_confidence: 0.91,
      predicted_severity: "MEDIUM",
      processed_at: new Date().toISOString(),
    });
  }, MOCK_DELAY_DONE_MS);

  return { id, processing_status: "PENDING", created_at: createdAt };
}

export async function mockGetMyReports(params: {
  limit: number;
  offset: number;
}): Promise<MyReportsResponse> {
  const newestFirst = Array.from(reports.values()).reverse();
  const items = newestFirst
    .slice(params.offset, params.offset + params.limit)
    .map(toListItem);
  return { items: items, total: newestFirst.length };
}

export async function mockGetReport(id: string): Promise<Report> {
  const report = reports.get(id);
  if (!report) {
    const error = new Error(`Report ${id} not found`);
    (error as Error & { status?: number }).status = 404;
    throw error;
  }
  return report;
}

function mockValidationError() {
  const error = new Error("Validation failed") as Error & {
    status?: number;
    errors?: { field: string; message: string }[];
  };
  error.status = 422;
  error.errors = [
    {
      field: "description",
      message: "Add a description, a photo, or both.",
    },
  ];
  return error;
}
