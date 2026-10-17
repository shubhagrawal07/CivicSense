import type {
  IssueStatus,
  MyReportListItem,
  MyReportsResponse,
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

seedDemoReports();

// Seeds a few reports in different states so /my-reports and the demo have
// something to show on first load. Submitting a report writes into this same
// Map, so live submissions show up in the list right next to these.
function seedDemoReports() {
  const seeds: Array<Pick<Report, "description" | "processing_status"> & {
    classification?: string;
    predicted_severity?: Report["predicted_severity"];
    error?: string;
  }> = [
    { description: "Large pothole on Main St", processing_status: "DONE", classification: "pothole", predicted_severity: "HIGH" },
    { description: "Streetlight out near the park", processing_status: "DONE", classification: "lighting", predicted_severity: "LOW" },
    { description: "Overflowing bin on 5th Ave", processing_status: "PENDING" },
    { description: "Graffiti on the underpass wall", processing_status: "PROCESSING" },
    { description: "Broken fence, reported but marked fail for demo", processing_status: "FAILED", error: "Mock failure: description contained \"fail\"." },
  ];

  seeds.forEach((seed, index) => {
    const id = String(nextId++);
    reports.set(id, {
      id,
      description: seed.description,
      image_path: null,
      latitude: 0,
      longitude: 0,
      processing_status: seed.processing_status,
      created_at: new Date(Date.now() - (seeds.length - index) * 3600_000).toISOString(),
      classification: seed.classification ?? null,
      predicted_severity: seed.predicted_severity ?? null,
      error: seed.error ?? null,
    });
  });
}

function issueStatusFor(id: string): IssueStatus {
  const order: IssueStatus[] = ["NEW", "IN_PROGRESS", "RESOLVED"];
  return order[Number(id) % order.length];
}

function toListItem(report: Report): MyReportListItem {
  const isDone = report.processing_status === "DONE";
  return {
    id: report.id,
    description_preview: report.description
      ? report.description.slice(0, 80)
      : null,
    thumbnail_url: report.image_path,
    created_at: report.created_at,
    processing_status: report.processing_status,
    category: isDone ? report.classification ?? null : null,
    severity_level: isDone ? report.predicted_severity ?? null : null,
    issue_id: isDone ? report.id : null,
    issue_status: isDone ? issueStatusFor(report.id) : null,
    report_count: isDone ? 1 : null,
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

export async function mockGetMyReports({
  limit = 20,
  offset = 0,
}: { limit?: number; offset?: number }): Promise<MyReportsResponse> {
  if (limit < 1 || limit > 100) {
    throw mockRangeError("limit", "limit must be between 1 and 100.");
  }
  if (offset < 0) {
    throw mockRangeError("offset", "offset must be 0 or more.");
  }

  const all = Array.from(reports.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
  const items = all.slice(offset, offset + limit).map(toListItem);
  return { items, total: all.length };
}

function mockRangeError(field: string, message: string) {
  const error = new Error("Validation failed") as Error & {
    status?: number;
    errors?: { field: string; message: string }[];
  };
  error.status = 422;
  error.errors = [{ field, message }];
  return error;
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
