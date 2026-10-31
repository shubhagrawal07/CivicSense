import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { getIssue } from "../api/issues";
import { parseApiError } from "../api/errors";
import type { Issue } from "../api/types";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { AuthoritySection } from "../components/issue/AuthoritySection";
import { IssueMap } from "../components/issue/IssueMap";
import { StatusHistory } from "../components/issue/StatusHistory";
import { issueStatusLabel } from "../components/report/StatusBadge";

type LoadState =
  | { kind: "loading" }
  | { kind: "notFound" }
  | { kind: "error"; message: string }
  | { kind: "ready"; issue: Issue };

function isNotFound(err: unknown): boolean {
  if (isAxiosError(err)) return err.response?.status === 404;
  return (err as { status?: number })?.status === 404;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

export function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    setState({ kind: "loading" });

    // ids are plain integers; anything else can't exist, so skip the request
    if (!id || !/^\d+$/.test(id)) {
      setState({ kind: "notFound" });
      return;
    }

    getIssue(id)
      .then((issue) => {
        if (active) setState({ kind: "ready", issue });
      })
      .catch((err) => {
        if (!active) return;
        if (isNotFound(err)) {
          setState({ kind: "notFound" });
        } else {
          setState({ kind: "error", message: parseApiError(err).message });
        }
      });

    return () => {
      active = false;
    };
  }, [id]);

  if (state.kind === "loading") {
    return <LoadingSpinner label="Loading issue…" />;
  }

  if (state.kind === "notFound") {
    return (
      <div>
        <h2>Issue not found</h2>
        <p>We couldn't find an issue with that id.</p>
        <Link to="/my-reports">Back to my reports</Link>
      </div>
    );
  }

  if (state.kind === "error") {
    return <ErrorBanner message={state.message} />;
  }

  const { issue } = state;

  return (
    <div>
      <h2>Issue #{issue.id}</h2>
      <dl>
        <dt>Category</dt>
        <dd>{issue.category}</dd>
        <dt>Severity</dt>
        <dd>{issue.severity ?? "Not yet available"}</dd>
        <dt>Status</dt>
        <dd>{issueStatusLabel(issue.status)}</dd>
        <dt>Supporting reports</dt>
        <dd>{issue.report_count}</dd>
        <dt>First reported</dt>
        <dd>{formatDate(issue.first_reported_at)}</dd>
        <dt>Last reported</dt>
        <dd>{formatDate(issue.last_reported_at)}</dd>
      </dl>

      <h3>Location</h3>
      <IssueMap lat={issue.location.lat} lng={issue.location.lng} />

      <h3>Status history</h3>
      <StatusHistory changes={issue.status_history} />

      <AuthoritySection issue={issue} />
    </div>
  );
}
