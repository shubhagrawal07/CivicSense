import { useState } from "react";
import { ConfirmationScreen } from "../components/report/ConfirmationScreen";
import { ReportForm } from "../components/report/ReportForm";

export function ReportNewPage() {
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);

  if (submittedReportId) {
    return (
      <ConfirmationScreen
        reportId={submittedReportId}
        onSubmitAnother={() => setSubmittedReportId(null)}
      />
    );
  }

  return (
    <div>
      <h1>Report a civic issue</h1>
      <ReportForm onSubmitted={setSubmittedReportId} />
    </div>
  );
}
