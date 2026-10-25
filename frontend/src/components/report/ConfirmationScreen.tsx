import { Link } from "react-router-dom";

interface ConfirmationScreenProps {
  reportId: string;
  onSubmitAnother: () => void;
}

export function ConfirmationScreen({
  reportId,
  onSubmitAnother,
}: ConfirmationScreenProps) {
  return (
    <div>
      <h2>Your report has been received and is being analysed</h2>
      <p>Report ID: {reportId}</p>
      <Link to={`/reports/${reportId}`}>View this report</Link>
      {}
      <Link to="/my-reports">My reports</Link>
      <button type="button" onClick={onSubmitAnother}>
        Submit another
      </button>
    </div>
  );
}
