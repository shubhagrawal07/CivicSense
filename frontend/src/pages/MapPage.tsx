import { useEffect, useState } from "react";
import { getHotspots } from "../api/hotspots";
import { getMapIssues } from "../api/map";
import { parseApiError } from "../api/errors";
import type { HotspotCell, MapFeatureCollection } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { IssueFilters } from "../components/filters/IssueFilters";
import { EMPTY_FILTERS, toMapIssuesFilters } from "../components/filters/filters";
import type { AppliedFilters } from "../components/filters/filters";
import { HotspotLayer } from "../components/map/HotspotLayer";
import { HOTSPOT_LEGEND } from "../components/map/hotspots";
import { IssuesMap } from "../components/map/IssuesMap";
import { MapLegend } from "../components/map/MapLegend";
import { SEVERITY_LEGEND } from "../components/map/severity";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: MapFeatureCollection };

function isFiltered(filters: AppliedFilters): boolean {
  return (
    filters.category !== "" ||
    filters.severity.length > 0 ||
    filters.status.length > 0 ||
    filters.from !== "" ||
    filters.to !== ""
  );
}

export function MapPage() {
  const [filters, setFilters] = useState<AppliedFilters>(EMPTY_FILTERS);
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [showHotspots, setShowHotspots] = useState(false);
  const [hotspots, setHotspots] = useState<HotspotCell[]>([]);

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

  useEffect(() => {
    if (!showHotspots) return;
    let active = true;
    getHotspots(filters.category || undefined)
      .then((cells) => {
        if (active) setHotspots(cells);
      })
      .catch(() => {
        if (active) setHotspots([]);
      });
    return () => {
      active = false;
    };
  }, [showHotspots, filters.category]);

  return (
    <div>
      <h2>Issue map</h2>
      <IssueFilters onApply={setFilters} />
      <label>
        <input
          type="checkbox"
          checked={showHotspots}
          onChange={(e) => setShowHotspots(e.target.checked)}
        />
        Show hotspots
      </label>
      {state.kind === "loading" && <LoadingSpinner label="Loading map…" />}
      {state.kind === "error" && <ErrorBanner message={state.message} />}
      {state.kind === "ready" && (
        <>
          <p>{state.data.features.length} issues</p>
          {state.data.features.length === 0 && (
            <p>{isFiltered(filters) ? "No issues match" : "No issues to show on the map yet"}</p>
          )}
          <IssuesMap features={state.data.features}>
            {showHotspots && <HotspotLayer cells={hotspots} />}
          </IssuesMap>
          <MapLegend entries={SEVERITY_LEGEND} />
          {showHotspots && (
            <>
              <MapLegend entries={HOTSPOT_LEGEND} />
              <p>
                Score adds up the issues in an area, counting serious and recent ones more heavily.
              </p>
            </>
          )}
        </>
      )}
    </div>
  );
}
