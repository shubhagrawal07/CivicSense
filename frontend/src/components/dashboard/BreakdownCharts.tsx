import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { parseApiError } from "../../api/errors";
import { getBreakdown } from "../../api/stats";
import type { Severity, StatsBreakdown } from "../../api/types";
import { ErrorBanner } from "../common/ErrorBanner";
import { LoadingSpinner } from "../common/LoadingSpinner";

const SEVERITY_COLORS: Record<Severity, string> = {
  LOW: "#2e7d32",
  MEDIUM: "#f9a825",
  HIGH: "#ef6c00",
  CRITICAL: "#c62828",
};
const SEVERITY_ORDER: Severity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const LABEL_STYLE = { fontSize: 12, fill: "#555" };

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: StatsBreakdown };

function ChartBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="chart-box">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function CategoryChart({ rows }: { rows: StatsBreakdown["by_category"] }) {
  if (rows.length === 0) return <p>No data</p>;

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, rows.length * 36 + 60)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 32, bottom: 24 }}>
        <XAxis
          type="number"
          allowDecimals={false}
          label={{ value: "Issues", position: "insideBottom", offset: -10, style: LABEL_STYLE }}
        />
        <YAxis type="category" dataKey="category" width={130} />
        <Tooltip />
        <Bar dataKey="count" name="Issues" fill="#1565c0" isAnimationActive={false}>
          <LabelList dataKey="count" position="right" />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function SeverityChart({ rows }: { rows: StatsBreakdown["by_severity"] }) {
  if (rows.length === 0) return <p>No data</p>;

  const counts = new Map(rows.map((row) => [row.severity, row.count]));
  const ordered = SEVERITY_ORDER.map((severity) => ({
    severity,
    count: counts.get(severity) ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={ordered} margin={{ top: 20, right: 16, left: 8, bottom: 24 }}>
        <XAxis
          dataKey="severity"
          label={{ value: "Severity", position: "insideBottom", offset: -10, style: LABEL_STYLE }}
        />
        <YAxis
          allowDecimals={false}
          label={{ value: "Issues", angle: -90, position: "insideLeft", style: LABEL_STYLE }}
        />
        <Tooltip />
        <Bar dataKey="count" name="Issues" isAnimationActive={false}>
          {ordered.map((row) => (
            <Cell key={row.severity} fill={SEVERITY_COLORS[row.severity]} />
          ))}
          <LabelList dataKey="count" position="top" />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function BreakdownCharts() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getBreakdown()
      .then((data) => {
        if (active) setState({ kind: "ready", data });
      })
      .catch((err) => {
        if (active) setState({ kind: "error", message: parseApiError(err).message });
      });
    return () => {
      active = false;
    };
  }, []);

  if (state.kind === "loading") {
    return <LoadingSpinner label="Loading charts…" />;
  }
  if (state.kind === "error") {
    return <ErrorBanner message={state.message} />;
  }

  return (
    <div className="chart-grid">
      <ChartBox title="Issues by category">
        <CategoryChart rows={state.data.by_category} />
      </ChartBox>
      <ChartBox title="Issues by severity">
        <SeverityChart rows={state.data.by_severity} />
      </ChartBox>
    </div>
  );
}
