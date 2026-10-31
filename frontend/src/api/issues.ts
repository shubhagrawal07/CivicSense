import { client } from "./client";
import { mockGetIssue } from "./mock/mockIssues";
import { env } from "../config/env";
import type { Issue } from "./types";

async function realGetIssue(id: string): Promise<Issue> {
  const { data } = await client.get<Issue>(`/issues/${id}`);
  return data;
}

export const getIssue: (id: string) => Promise<Issue> = env.useMockApi
  ? mockGetIssue
  : realGetIssue;
