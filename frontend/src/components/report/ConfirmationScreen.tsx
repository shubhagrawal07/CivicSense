import { Link } from "react-router-dom";

interface ConfirmationScreenProps {
  reportId: string;
  onSubmitAnother: () => void;
}

export function ConfirmationScreen({ reportId, onSubmitAnother }: ConfirmationScreenProps) {
  return (
    <div>
      <h2>Your report has been received and is being analysed</h2>
      <p>Report ID: {reportId}</p>
      <div className="button-row">
        <Link to={`/reports/${reportId}`} className="nav-button">
          View this report
        </Link>
        <Link to="/my-reports" className="nav-button">
          My reports
        </Link>
        <button type="button" className="nav-button" onClick={onSubmitAnother}>
          Submit another
        </button>
      </div>
    </div>
  );
}
