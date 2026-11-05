import { client } from "./client";
import { env } from "../config/env";
import type { StatsSummary } from "./types";

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
