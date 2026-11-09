import { client } from "./client";
import { env } from "../config/env";
import type { DataQuality } from "./types";

async function realGetDataQuality(): Promise<DataQuality> {
  const { data } = await client.get<DataQuality>("/admin/data-quality");
  return data;
}

async function mockGetDataQuality(): Promise<DataQuality> {
  return {
    reports_without_description: 0,
    reports_without_image: 1,
    reports_failed_processing: 0,
    issues_outside_any_ward: null,
    contacts_unverified: 9,
    contacts_older_than_90_days: 0,
  };
}

export const getDataQuality: () => Promise<DataQuality> = env.useMockApi
  ? mockGetDataQuality
  : realGetDataQuality;
