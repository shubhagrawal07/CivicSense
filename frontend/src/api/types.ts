// Mirrors the backend `Report` model (backend/app/models/report.py) and its
// enums (backend/app/models/enums.py) as closely as possible. SL-11 has not
// published a finalized API contract yet — keep this minimal and extend it
// as SL-11/SL-16 land real fields, rather than guessing ahead of them.

export type ProcessingStatus = "PENDING" | "PROCESSING" | "DONE" | "FAILED";

export type ClassificationSource = "TEXT" | "IMAGE" | "BOTH";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface SubmitReportPayload {
  description?: string;
  image?: File | null;
  latitude: number;
  longitude: number;
}

export interface SubmitReportResponse {
  id: string;
  processing_status: ProcessingStatus;
  created_at: string;
}

export interface Report {
  id: string;
  description?: string | null;
  image_path?: string | null;
  latitude: number;
  longitude: number;
  processing_status: ProcessingStatus;
  error?: string | null;

  classification?: string | null;
  classification_confidence?: number | null;
  classification_source?: ClassificationSource | null;
  conflict?: boolean;
  needs_review?: boolean;

  predicted_department_id?: number | null;
  department_confidence?: number | null;
  predicted_severity?: Severity | null;

  created_at: string;
  processed_at?: string | null;
}

export type IssueStatus = "NEW" | "IN_PROGRESS" | "RESOLVED";

export interface MyReportListItem {
  id: string;
  description_preview?: string | null;
  thumbnail_url?: string | null;
  created_at: string;
  processing_status: ProcessingStatus;
  category?: string | null;
  severity_level?: Severity | null;
  issue_id?: string | null;
  issue_status?: IssueStatus | null;
  report_count?: number | null;
}

export interface MyReportsResponse {
  items: MyReportListItem[];
  total: number;
}

export interface ApiFieldError {
  field: string;
  message: string;
}

export interface ApiErrorResponse {
  detail?: string;
  errors?: ApiFieldError[];
}
