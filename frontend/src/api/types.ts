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

  issue?: { id: number | string } | null;

  created_at: string;
  processed_at?: string | null;
}

export type IssueStatus =
  | "NEW"
  | "UNDER_REVIEW"
  | "CLASSIFIED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "VERIFIED"
  | "CLOSED"
  | "DUPLICATE"
  | "REJECTED"
  | "ESCALATED"
  | "REOPENED";

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

export type UserRole = "CITIZEN" | "OFFICER" | "ADMIN";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResult {
  token: string;
  user: User;
}

export interface IssueContact {
  type: string;
  value: string;
  source_url: string | null;
  last_verified_at: string | null;
  verified: boolean;
}

export interface IssueStatusChange {
  status: IssueStatus;
  changed_at: string;
  note: string | null;
}

export interface Issue {
  id: number;
  category: string;
  severity: Severity | null;
  status: IssueStatus;
  location: { lat: number; lng: number };
  report_count: number;
  first_reported_at: string;
  last_reported_at: string;
  department: { id: number; name: string } | null;
  authority: { id: number; name: string; jurisdiction: string } | null;
  contacts: IssueContact[];
  status_history: IssueStatusChange[];
}
