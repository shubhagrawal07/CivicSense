import { useState } from "react";
import { Link } from "react-router-dom";
import { useMyReportsPolling } from "../hooks/useMyReportsPolling";
import { MyReportsList } from "../components/report/MyReportsList";
import { Pagination } from "../components/common/Pagination";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorBanner } from "../components/common/ErrorBanner";

const LIMIT = 20;

export function MyReportsPage() {
  const [offset, setOffset] = useState(0);
  const { items, total, isLoading, timedOut, error } = useMyReportsPolling(LIMIT, offset);

  if (isLoading && items.length === 0) {
    return <LoadingSpinner label="Loading your reports…" />;
  }

  if (error) {
    return <ErrorBanner message={error} />;
  }

  if (total === 0) {
    return (
      <div>
        <p>You haven't reported anything yet.</p>
        <Link to="/report/new">Report an issue</Link>
      </div>
    );
  }

  return (
    <div>
      <h1>My reports</h1>
      <MyReportsList items={items} />
      <Pagination total={total} limit={LIMIT} offset={offset} onOffsetChange={setOffset} />
      {timedOut && <p>Taking longer than usual. Check back soon.</p>}
    </div>
  );
}
