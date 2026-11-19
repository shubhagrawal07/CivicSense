import type { MapIssuesFilters } from "../../api/map";
import type { IssueStatusBucket, Severity } from "../../api/types";

export interface AppliedFilters {
  category: string;
  severity: Severity[];
  status: IssueStatusBucket[];
  from: string;
  to: string;
}

export const EMPTY_FILTERS: AppliedFilters = {
  category: "",
  severity: [],
  status: [],
  from: "",
  to: "",
};

export const SEVERITY_OPTIONS: Severity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const STATUS_OPTIONS: IssueStatusBucket[] = ["open", "in_progress", "resolved"];

export const CATEGORY_OPTIONS = [
  "pothole",
  "garbage",
  "drainage_sewage",
  "road_obstruction",
  "streetlight",
  "damaged_infrastructure",
  "water_leakage",
  "open_manhole",
  "electricity_outage",
  "other",
];

export function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function toMapIssuesFilters(filters: AppliedFilters): MapIssuesFilters {
  return {
    category: filters.category || undefined,
    severity: filters.severity.length ? filters.severity : undefined,
    status: filters.status.length ? filters.status : undefined,
    from: filters.from || undefined,
    to: filters.to || undefined,
  };
}

export function buildFilterQuery(filters: AppliedFilters): string {
  const params = new URLSearchParams();
  if (filters.category) params.append("category", filters.category);
  for (const value of filters.severity) params.append("severity", value);
  for (const value of filters.status) params.append("status", value);
  if (filters.from) params.append("from", filters.from);
  if (filters.to) params.append("to", filters.to);
  return params.toString();
}
