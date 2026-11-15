import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getTrend } from "../api/stats";
import { parseApiError } from "../api/errors";
import type { TrendInterval, TrendPoint } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; points: TrendPoint[] };

const CATEGORY_OPTIONS = [
  "pothole",
  "garbage",
  "drainage_sewage",
  "road_obstruction",
  "streetlight",
  "damaged_infrastructure",
  "water_leakage",
  "open_manhole",
  "electricity_outage",
  "other",
];

const AXIS_LABEL_STYLE = { fontSize: 12, fill: "#555" };

export function TrendsPage() {
  const [interval, setInterval] = useState<TrendInterval>("week");
  const [category, setCategory] = useState("");
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    setState({ kind: "loading" });
    getTrend(interval, category)
      .then((points) => {
        if (active) setState({ kind: "ready", points });
      })
      .catch((err) => {
        if (active) setState({ kind: "error", message: parseApiError(err).message });
      });
    return () => {
      active = false;
    };
  }, [interval, category]);

  return (
    <div>
      <h2>Trends</h2>
      <div className="trend-controls">
        <div className="interval-toggle">
          <button
            type="button"
            aria-pressed={interval === "day"}
            onClick={() => setInterval("day")}
          >
            Day
          </button>
          <button
            type="button"
            aria-pressed={interval === "week"}
            onClick={() => setInterval("week")}
          >
            Week
          </button>
        </div>
        <select
          aria-label="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {CATEGORY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      {state.kind === "loading" && <LoadingSpinner label="Loading trend…" />}
      {state.kind === "error" && <ErrorBanner message={state.message} />}
      {state.kind === "ready" && state.points.length === 0 && <p>No data for this selection</p>}
      {state.kind === "ready" && state.points.length > 0 && (
        <section className="chart-box">
          <h3>Issues reported per {interval}</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={state.points} margin={{ top: 8, right: 24, left: 8, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="period"
                label={{
                  value: interval === "week" ? "Week starting" : "Date",
                  position: "insideBottom",
                  offset: -10,
                  style: AXIS_LABEL_STYLE,
                }}
              />
              <YAxis
                allowDecimals={false}
                label={{
                  value: "Issues",
                  angle: -90,
                  position: "insideLeft",
                  style: AXIS_LABEL_STYLE,
                }}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                name="Issues"
                stroke="#1565c0"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>
      )}
    </div>
  );
}
