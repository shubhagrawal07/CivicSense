import { isAxiosError } from "axios";
import type { ApiErrorResponse } from "./types";

export interface ParsedApiError {
  status?: number;
  message: string;
  fieldErrors: Record<string, string>;
}

export function parseApiError(err: unknown): ParsedApiError {
  if (!isAxiosError<ApiErrorResponse>(err) || !err.response) {
    return { message: "Could not reach the server. Try again.", fieldErrors: {} };
  }

  const { status, data } = err.response;
  const fieldErrors: Record<string, string> = {};
  for (const item of data?.errors ?? []) {
    fieldErrors[item.field] = item.message;
  }
  return {
    status,
    message: typeof data?.detail === "string" ? data.detail : "Something went wrong.",
    fieldErrors,
  };
}
