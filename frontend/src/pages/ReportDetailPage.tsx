import { useParams } from "react-router-dom";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ResultCard } from "../components/report/ResultCard";
import { useReportPolling } from "../hooks/useReportPolling";

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { report, isLoading, timedOut, error } = useReportPolling(id ?? "");

  if (!id) {
    return <ErrorBanner message="No report id given." />;
  }

  if (error) {
    return <ErrorBanner message={error} />;
  }

  if (isLoading && !report) {
    return <LoadingSpinner label="Loading report…" />;
  }

  if (!report) {
    return <LoadingSpinner label="Loading report…" />;
  }

  if (report.processing_status === "FAILED") {
    return <ErrorBanner message={report.error ?? "Analysis failed."} />;
  }

  if (report.processing_status === "DONE") {
    return <ResultCard report={report} />;
  }

  if (timedOut) {
    return <p>This is taking longer than usual. Check back later.</p>;
  }

  return <LoadingSpinner label="Analysing…" />;
}
