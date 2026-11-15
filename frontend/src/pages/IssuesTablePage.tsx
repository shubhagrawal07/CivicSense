import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMapIssues } from "../api/map";
import { parseApiError } from "../api/errors";
import { env } from "../config/env";
import type { MapFeature, MapFeatureCollection } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { Pagination } from "../components/common/Pagination";
import { IssueFilters } from "../components/filters/IssueFilters";
import { EMPTY_FILTERS, toMapIssuesFilters } from "../components/filters/filters";
import type { AppliedFilters } from "../components/filters/filters";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: MapFeatureCollection };

interface SortState {
  key: "id" | "category" | "severity" | "status" | "report_count" | "last_reported_at";
  direction: "asc" | "desc";
}

const PAGE_SIZE = 25;

export function sortFeatures(features: MapFeature[], sort: SortState): MapFeature[] {
  const sorted = [...features].sort((a, b) => {
    const left = a.properties[sort.key];
    const right = b.properties[sort.key];
    if (left === right) return 0;
    if (left === null) return -1;
    if (right === null) return 1;
    return left < right ? -1 : 1;
  });
  if (sort.direction === "desc") sorted.reverse();
  return sorted;
}

export function buildFilterQuery(filters: AppliedFilters): string {
  const params = new URLSearchParams();
  if (filters.category) params.append("category", filters.category);
  for (const value of filters.severity) params.append("severity", value);
  for (const value of filters.status) params.append("status", value);
  if (filters.from) params.append("from", filters.from);
  if (filters.to) params.append("to", filters.to);
  return params.toString();
}

export function IssuesTablePage() {
  const [filters, setFilters] = useState<AppliedFilters>(EMPTY_FILTERS);
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [sort, setSort] = useState<SortState>({
    key: "last_reported_at",
    direction: "desc",
  });
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    let active = true;
    setState({ kind: "loading" });
    getMapIssues(toMapIssuesFilters(filters))
      .then((data) => {
        if (active) setState({ kind: "ready", data });
      })
      .catch((err) => {
        if (active) setState({ kind: "error", message: parseApiError(err).message });
      });
    return () => {
      active = false;
    };
  }, [filters]);

  function applyFilters(applied: AppliedFilters) {
    setOffset(0);
    setFilters(applied);
  }

  function toggleSort(key: SortState["key"]) {
    setSort((current) =>
      current.key === key
        ? { key, direction: current.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" },
    );
  }

  const csvUrl = `${env.apiBaseUrl}/issues/export.csv?${buildFilterQuery(filters)}`;

  return (
    <div>
      <h2>Issues</h2>
      <IssueFilters onApply={applyFilters} />
      <p>
        <a href={csvUrl}>Download CSV</a>
      </p>

      {state.kind === "loading" && <LoadingSpinner label="Loading issues…" />}
      {state.kind === "error" && <ErrorBanner message={state.message} />}
      {state.kind === "ready" && state.data.features.length === 0 && <p>No issues found</p>}
      {state.kind === "ready" && state.data.features.length > 0 && (
        <>
          <table className="issues-table">
            <thead>
              <tr>
                <th onClick={() => toggleSort("id")}>Id</th>
                <th onClick={() => toggleSort("category")}>Category</th>
                <th onClick={() => toggleSort("severity")}>Severity</th>
                <th onClick={() => toggleSort("status")}>Status</th>
                <th onClick={() => toggleSort("report_count")}>Reports</th>
                <th onClick={() => toggleSort("last_reported_at")}>Last reported</th>
              </tr>
            </thead>
            <tbody>
              {sortFeatures(state.data.features, sort)
                .slice(offset, offset + PAGE_SIZE)
                .map((feature) => (
                  <tr key={feature.properties.id}>
                    <td>
                      <Link to={`/issues/${feature.properties.id}`}>{feature.properties.id}</Link>
                    </td>
                    <td>{feature.properties.category}</td>
                    <td>{feature.properties.severity ?? "—"}</td>
                    <td>{feature.properties.status}</td>
                    <td>{feature.properties.report_count}</td>
                    <td>{feature.properties.last_reported_at}</td>
                  </tr>
                ))}
            </tbody>
          </table>
          <Pagination
            total={state.data.features.length}
            limit={PAGE_SIZE}
            offset={offset}
            onOffsetChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
