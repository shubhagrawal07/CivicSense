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
  classification_source?: ClassificationSource | null;
  conflict?: boolean;

  department?: { id: number; name: string } | null;
  predicted_severity?: Severity | null;

  issue?: { id: number | string } | null;

  created_at: string;
}

export interface ReportDetailResponse {
  id: number;
  description: string | null;
  image_url: string | null;
  location: { lat: number; lng: number };
  created_at: string;
  processing_status: ProcessingStatus;
  error: string | null;
  classification: {
    category: string;
    source: ClassificationSource | null;
    conflict: boolean;
  } | null;
  department: { id: number; name: string } | null;
  severity: { level: Severity } | null;
  issue: { id: number } | null;
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

export type IssueStatusBucket = "open" | "in_progress" | "resolved";

export interface MapIssueProperties {
  id: number;
  category: string;
  severity: Severity | null;
  status: IssueStatus;
  report_count: number;
  last_reported_at: string;
}

export interface MapFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: MapIssueProperties;
}

export interface MapFeatureCollection {
  type: "FeatureCollection";
  features: MapFeature[];
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

export interface DataQuality {
  reports_without_description: number;
  reports_without_image: number;
  reports_failed_processing: number;
  issues_outside_any_ward: number | null;
  contacts_unverified: number;
  contacts_older_than_90_days: number;
}

export interface StatsSummary {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  avg_resolution_days: number | null;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface SeverityCount {
  severity: Severity;
  count: number;
}

export interface StatsBreakdown {
  by_category: CategoryCount[];
  by_severity: SeverityCount[];
}
