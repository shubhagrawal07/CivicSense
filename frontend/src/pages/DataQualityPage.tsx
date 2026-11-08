import { useEffect, useState } from "react";
import { getDataQuality } from "../api/admin";
import { parseApiError } from "../api/errors";
import type { DataQuality } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: DataQuality };

const CHECKS: { key: keyof DataQuality; label: string }[] = [
  { key: "reports_without_description", label: "Reports without a description" },
  { key: "reports_without_image", label: "Reports without an image" },
  { key: "reports_failed_processing", label: "Reports that failed processing" },
  { key: "issues_outside_any_ward", label: "Issues outside any ward" },
  { key: "contacts_unverified", label: "Unverified contacts" },
  { key: "contacts_older_than_90_days", label: "Contacts verified over 90 days ago" },
];

export function DataQualityPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getDataQuality()
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
    return <LoadingSpinner label="Loading data quality…" />;
  }
  if (state.kind === "error") {
    return <ErrorBanner message={state.message} />;
  }

  return (
    <div>
      <h2>Data quality</h2>
      <table className="quality-table">
        <thead>
          <tr>
            <th>Check</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {CHECKS.map((check) => {
            const count = state.data[check.key];
            let badgeClass = "badge badge--grey";
            if (count === 0) badgeClass = "badge badge--green";
            if (count !== null && count > 0) badgeClass = "badge badge--orange";

            return (
              <tr key={check.key}>
                <td>{check.label}</td>
                <td>
                  <span className={badgeClass}>{count === null ? "N/A" : count}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
