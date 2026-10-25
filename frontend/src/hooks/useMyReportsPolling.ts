import { useEffect, useState } from "react";
import { getMyReports } from "../api/reports";
import type { MyReportListItem } from "../api/types";

const POLL_INTERVAL_MS = 3000;
const TIMEOUT_MS = 2 * 60 * 1000;

export function useMyReportsPolling(limit: number, offset: number) {
  const [items, setItems] = useState<MyReportListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [timedOut, setTimedOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const startedAt = Date.now();

    setIsLoading(true);
    setTimedOut(false);
    setError(null);

    async function tick() {
      try {
        const response = await getMyReports({ limit, offset });
        if (!active) return;
        setItems(response.items);
        setTotal(response.total);
        setIsLoading(false);

        const anyPending = response.items.some(
          (item) =>
            item.processing_status === "PENDING" ||
            item.processing_status === "PROCESSING",
        );
        if (!anyPending) return;

        if (Date.now() - startedAt > TIMEOUT_MS) {
          setTimedOut(true);
          return;
        }

        timer = setTimeout(tick, POLL_INTERVAL_MS);
      } catch (err) {
        if (!active) return;
        setIsLoading(false);
        setError(err instanceof Error ? err.message : "Failed to load your reports.");
      }
    }

    tick();

    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [limit, offset]);

  return { items, total, isLoading, timedOut, error };
}
