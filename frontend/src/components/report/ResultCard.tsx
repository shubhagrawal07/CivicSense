import { Link } from "react-router-dom";
import type { Report } from "../../api/types";

const SOURCE_LABEL: Record<string, string> = {
  TEXT: "the description",
  IMAGE: "the photo",
  BOTH: "both the description and the photo",
};

export function ResultCard({ report }: { report: Report }) {
  return (
    <div>
      <h2>Result</h2>
      <dl>
        <dt>Category</dt>
        <dd>
          {report.classification ?? "Not yet available"}
          {report.classification_source && (
            <> — determined from {SOURCE_LABEL[report.classification_source]}</>
          )}
          {report.conflict && <span> (text and photo disagreed)</span>}
        </dd>

        <dt>Severity</dt>
        <dd>{report.predicted_severity ?? "Not yet available"}</dd>

        <dt>Department</dt>
        <dd>
          {report.predicted_department_id
            ? `Department #${report.predicted_department_id}`
            : "Not yet available"}
        </dd>
      </dl>
      {report.issue && (
        <p>
          <Link to={`/issues/${report.issue.id}`}>
            View the issue this report belongs to
          </Link>
        </p>
      )}
    </div>
  );
}
