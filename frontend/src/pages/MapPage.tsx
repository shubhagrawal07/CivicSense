import { useEffect, useState } from "react";
import { getMapIssues } from "../api/map";
import { parseApiError } from "../api/errors";
import type { MapFeatureCollection } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { IssuesMap } from "../components/map/IssuesMap";
import { MapLegend } from "../components/map/MapLegend";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: MapFeatureCollection };

export function MapPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getMapIssues({})
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

  return (
    <div>
      <h2>Issue map</h2>
      {state.kind === "loading" && <LoadingSpinner label="Loading map…" />}
      {state.kind === "error" && <ErrorBanner message={state.message} />}
      {state.kind === "ready" && (
        <>
          {state.data.features.length === 0 && <p>No issues to show on the map yet</p>}
          <IssuesMap features={state.data.features} />
          <MapLegend />
        </>
      )}
    </div>
  );
}
