
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
