import { client } from "./client";
import type {
  IssueStatusBucket,
  MapFeatureCollection,
  Severity,
} from "./types";

export interface MapIssuesFilters {
  category?: string;
  severity?: Severity[];
  status?: IssueStatusBucket[];
  from?: string;
  to?: string;
}

function buildQuery(filters: MapIssuesFilters): string {
  const params = new URLSearchParams();
  if (filters.category) params.append("category", filters.category);
  for (const value of filters.severity ?? []) params.append("severity", value);
  for (const value of filters.status ?? []) params.append("status", value);
  if (filters.from) params.append("from", filters.from);
  if (filters.to) params.append("to", filters.to);
  return params.toString();
}

export async function getMapIssues(
  filters: MapIssuesFilters,
): Promise<MapFeatureCollection> {
  const { data } = await client.get<MapFeatureCollection>(
    `/map/issues?${buildQuery(filters)}`,
  );
  return data;
}
