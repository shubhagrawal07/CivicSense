import { client } from "./client";
import { env } from "../config/env";
import type { StatsBreakdown, StatsSummary, TrendInterval, TrendPoint } from "./types";

async function realGetSummary(): Promise<StatsSummary> {
  const { data } = await client.get<StatsSummary>("/stats/summary");
  return data;
}

// same shape the backend sends, for running the page without it
async function mockGetSummary(): Promise<StatsSummary> {
  return {
    total: 42,
    open: 20,
    in_progress: 9,
    resolved: 11,
    avg_resolution_days: 6.4,
  };
}

export const getSummary: () => Promise<StatsSummary> = env.useMockApi
  ? mockGetSummary
  : realGetSummary;

async function realGetBreakdown(): Promise<StatsBreakdown> {
  const { data } = await client.get<StatsBreakdown>("/stats/breakdown");
  return data;
}

async function mockGetBreakdown(): Promise<StatsBreakdown> {
  return {
    by_category: [
      { category: "pothole", count: 14 },
      { category: "garbage", count: 11 },
      { category: "water leakage", count: 8 },
      { category: "streetlight", count: 5 },
      { category: "drainage", count: 4 },
    ],
    by_severity: [
      { severity: "HIGH", count: 15 },
      { severity: "MEDIUM", count: 17 },
      { severity: "LOW", count: 7 },
      { severity: "CRITICAL", count: 3 },
    ],
  };
}

export const getBreakdown: () => Promise<StatsBreakdown> = env.useMockApi
  ? mockGetBreakdown
  : realGetBreakdown;

async function realGetTrend(interval: TrendInterval, category: string): Promise<TrendPoint[]> {
  const params: Record<string, string> = { interval };
  if (category) params.category = category;
  const { data } = await client.get<TrendPoint[]>("/stats/trend", { params });
  return data;
}

async function mockGetTrend(interval: TrendInterval, category: string): Promise<TrendPoint[]> {
  const weekly = [
    ["2026-09-28", 6],
    ["2026-10-05", 9],
    ["2026-10-12", 14],
    ["2026-10-19", 11],
    ["2026-10-26", 18],
    ["2026-11-02", 15],
  ] as const;
  const daily = [
    ["2026-11-02", 2],
    ["2026-11-03", 4],
    ["2026-11-04", 1],
    ["2026-11-06", 5],
    ["2026-11-07", 3],
  ] as const;
  // a chosen category shows a smaller series so the change is visible
  const scale = category ? 0.4 : 1;
  const rows = interval === "day" ? daily : weekly;
  return rows.map(([period, count]) => ({ period, count: Math.round(count * scale) }));
}

export const getTrend: (interval: TrendInterval, category: string) => Promise<TrendPoint[]> =
  env.useMockApi ? mockGetTrend : realGetTrend;
