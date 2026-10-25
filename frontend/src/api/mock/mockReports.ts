import type {
  Report,
  SubmitReportPayload,
  SubmitReportResponse,
} from "../types";

const MOCK_DELAY_PROCESSING_MS = 1500;
const MOCK_DELAY_DONE_MS = 6000;

const reports = new Map<string, Report>();
let nextId = 1;

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
