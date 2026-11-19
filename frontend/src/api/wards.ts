import { client } from "./client";
import { env } from "../config/env";
import type { WardCount, WardFeatureCollection } from "./types";

async function realGetWardBoundaries(): Promise<WardFeatureCollection> {
  const { data } = await client.get<WardFeatureCollection>("/jurisdictions", {
    params: { type: "ward" },
  });
  return data;
}

async function realGetWardCounts(category: string): Promise<WardCount[]> {
  const params: Record<string, string> = {};
  if (category) params.category = category;
  const { data } = await client.get<WardCount[]>("/stats/by-ward", { params });
  return data;
}

async function mockGetWardBoundaries(): Promise<WardFeatureCollection> {
  const square = (west: number, south: number): [number, number][][] => [
    [
      [west, south],
      [west + 0.05, south],
      [west + 0.05, south + 0.05],
      [west, south + 0.05],
      [west, south],
    ],
  ];
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: square(72.82, 19.0) },
        properties: { id: 1, name: "A Ward", type: "ward", authority_name: null },
      },
      {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: square(72.88, 19.0) },
        properties: { id: 2, name: "B Ward", type: "ward", authority_name: null },
      },
      {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: square(72.82, 19.06) },
        properties: { id: 3, name: "C Ward", type: "ward", authority_name: null },
      },
    ],
  };
}

async function mockGetWardCounts(category: string): Promise<WardCount[]> {
  const scale = category ? 0.4 : 1;
  const rows = [
    { ward_id: 1, ward_name: "A Ward", issue_count: 34, open_count: 12, high_severity_count: 5 },
    { ward_id: 2, ward_name: "B Ward", issue_count: 10, open_count: 4, high_severity_count: 1 },
    { ward_id: 3, ward_name: "C Ward", issue_count: 0, open_count: 0, high_severity_count: 0 },
  ];
  return rows.map((row) => ({
    ...row,
    issue_count: Math.round(row.issue_count * scale),
    open_count: Math.round(row.open_count * scale),
  }));
}

export const getWardBoundaries: () => Promise<WardFeatureCollection> = env.useMockApi
  ? mockGetWardBoundaries
  : realGetWardBoundaries;

export const getWardCounts: (category: string) => Promise<WardCount[]> = env.useMockApi
  ? mockGetWardCounts
  : realGetWardCounts;
