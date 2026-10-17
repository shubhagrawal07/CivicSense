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
      {/* /my-reports doesn't exist until SL-27 lands; linking now keeps the
          confirmation screen's shape stable for that ticket to slot into. */}
      <Link to="/my-reports">My reports</Link>
      <button type="button" onClick={onSubmitAnother}>
        Submit another
      </button>
    </div>
  );
}
