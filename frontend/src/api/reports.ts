import { client } from "./client";
import {
  mockGetMyReports,
  mockGetReport,
  mockSubmitReport,
} from "./mock/mockReports";
import { env } from "../config/env";
import type {
  MyReportsResponse,
  Report,
  SubmitReportPayload,
  SubmitReportResponse,
} from "./types";

async function realSubmitReport(
  payload: SubmitReportPayload,
): Promise<SubmitReportResponse> {
  const formData = new FormData();
  if (payload.description) formData.append("description", payload.description);
  if (payload.image) formData.append("image", payload.image);
  formData.append("latitude", String(payload.latitude));
  formData.append("longitude", String(payload.longitude));

  const { data } = await client.post<SubmitReportResponse>(
    "/reports",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

async function realGetReport(id: string): Promise<Report> {
  const { data } = await client.get<Report>(`/reports/${id}`);
  return data;
}

export const submitReport: (
  payload: SubmitReportPayload,
) => Promise<SubmitReportResponse> = env.useMockApi
  ? mockSubmitReport
  : realSubmitReport;

export const getReport: (id: string) => Promise<Report> = env.useMockApi
  ? mockGetReport
  : realGetReport;

async function realGetMyReports(params: {
  limit: number;
  offset: number;
}): Promise<MyReportsResponse> {
  const { data } = await client.get<MyReportsResponse>("/reports/mine", {
    params,
  });
  return data;
}

export const getMyReports: (params: {
  limit: number;
  offset: number;
}) => Promise<MyReportsResponse> = env.useMockApi
  ? mockGetMyReports
  : realGetMyReports;
