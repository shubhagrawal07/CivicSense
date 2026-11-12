import { useEffect, useState } from "react";
import { getSummary } from "../api/stats";
import { parseApiError } from "../api/errors";
import type { StatsSummary } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; summary: StatsSummary };

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__label">{label}</div>
    </div>
  );
}

export function DashboardPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getSummary()
      .then((summary) => {
        if (active) setState({ kind: "ready", summary });
      })
      .catch((err) => {
        if (active) setState({ kind: "error", message: parseApiError(err).message });
      });
    return () => {
      active = false;
    };
  }, []);

  if (state.kind === "loading") {
    return <LoadingSpinner label="Loading dashboard…" />;
  }
  if (state.kind === "error") {
    return <ErrorBanner message={state.message} />;
  }

  const { summary } = state;
  const avg = summary.avg_resolution_days === null ? "N/A" : String(summary.avg_resolution_days);

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="stat-row">
        <StatCard label="Total issues" value={String(summary.total)} />
        <StatCard label="Open" value={String(summary.open)} />
        <StatCard label="In progress" value={String(summary.in_progress)} />
        <StatCard label="Resolved" value={String(summary.resolved)} />
        <StatCard label="Avg resolution (days)" value={avg} />
      </div>
    </div>
  );
}
