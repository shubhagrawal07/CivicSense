import type { MapFeature } from "../api/types";

export interface SortState {
  key: "id" | "category" | "severity" | "status" | "report_count" | "last_reported_at";
  direction: "asc" | "desc";
}

export function sortFeatures(features: MapFeature[], sort: SortState): MapFeature[] {
  const sorted = [...features].sort((a, b) => {
    const left = a.properties[sort.key];
    const right = b.properties[sort.key];
    if (left === right) return 0;
    if (left === null) return -1;
    if (right === null) return 1;
    return left < right ? -1 : 1;
  });
  if (sort.direction === "desc") sorted.reverse();
  return sorted;
}
