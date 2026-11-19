import { useEffect, useState } from "react";
import { getWardBoundaries, getWardCounts } from "../api/wards";
import { parseApiError } from "../api/errors";
import type { WardCount, WardFeatureCollection } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { WardLegend } from "../components/map/WardLegend";
import { WardMap } from "../components/map/WardMap";
import { buildWardRanges } from "../components/map/wardColours";

type LoadState<T> =
  { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; data: T };

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

export function WardMapPage() {
  const [category, setCategory] = useState("");
  const [wards, setWards] = useState<LoadState<WardFeatureCollection>>({ kind: "loading" });
  const [counts, setCounts] = useState<LoadState<WardCount[]>>({ kind: "loading" });

  useEffect(() => {
    getWardBoundaries()
      .then((data) => setWards({ kind: "ready", data }))
      .catch((err) => setWards({ kind: "error", message: parseApiError(err).message }));
  }, []);

  useEffect(() => {
    let active = true;
    setCounts({ kind: "loading" });
    getWardCounts(category)
      .then((data) => {
        if (active) setCounts({ kind: "ready", data });
      })
      .catch((err) => {
        if (active) setCounts({ kind: "error", message: parseApiError(err).message });
      });
    return () => {
      active = false;
    };
  }, [category]);

  let content;
  if (wards.kind === "error") {
    content = <ErrorBanner message={wards.message} />;
  } else if (counts.kind === "error") {
    content = <ErrorBanner message={counts.message} />;
  } else if (wards.kind === "loading" || counts.kind === "loading") {
    content = <LoadingSpinner label="Loading ward map…" />;
  } else {
    const highest = Math.max(0, ...counts.data.map((row) => row.issue_count));
    const ranges = buildWardRanges(highest);
    content = (
      <>
        <WardMap key={category} wards={wards.data} counts={counts.data} ranges={ranges} />
        <WardLegend ranges={ranges} />
      </>
    );
  }

  return (
    <div>
      <h2>Ward map</h2>
      <div className="trend-controls">
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
      {content}
    </div>
  );
}
