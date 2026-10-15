import { useEffect, useState } from "react";
import { getReport } from "../api/reports";
import type { Report } from "../api/types";

const POLL_INTERVAL_MS = 3000;
const TIMEOUT_MS = 2 * 60 * 1000;

interface UseReportPollingResult {
  report: Report | null;
  isLoading: boolean;
  timedOut: boolean;
  error: string | null;
}

export function useReportPolling(id: string): UseReportPollingResult {
  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timedOut, setTimedOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const startedAt = Date.now();

    async function tick() {
      try {
        const current = await getReport(id);
        if (!active) return;
        setReport(current);
        setIsLoading(false);

        if (
          current.processing_status === "DONE" ||
          current.processing_status === "FAILED"
        ) {
          return;
        }

        if (Date.now() - startedAt > TIMEOUT_MS) {
          setTimedOut(true);
          return;
        }

        timer = setTimeout(tick, POLL_INTERVAL_MS);
      } catch (err) {
        if (!active) return;
        setIsLoading(false);
        setError(err instanceof Error ? err.message : "Failed to load report.");
      }
    }

    tick();

    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  return { report, isLoading, timedOut, error };
}
