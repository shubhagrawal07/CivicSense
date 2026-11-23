import { FormEvent, useState } from "react";
import { updateIssueStatus } from "../../api/admin";
import { parseApiError } from "../../api/errors";
import type { IssueStatus } from "../../api/types";
import { ISSUE_STATUS_LABEL } from "../report/statusLabels";

interface StatusFormProps {
  issueId: number;
  currentStatus: IssueStatus;
  onUpdated: () => void;
}

export function StatusForm({ issueId, currentStatus, onUpdated }: StatusFormProps) {
  const [status, setStatus] = useState<IssueStatus>(currentStatus);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await updateIssueStatus(issueId, status, note.trim());
      setNote("");
      onUpdated();
    } catch (err) {
      setError(parseApiError(err).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="status-select">New status</label>
        <select
          id="status-select"
          value={status}
          onChange={(event) => setStatus(event.target.value as IssueStatus)}
        >
          {Object.entries(ISSUE_STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="status-note">Note (optional)</label>
        <textarea
          id="status-note"
          value={note}
          maxLength={1000}
          onChange={(event) => setNote(event.target.value)}
        />
      </div>
      {error && <p role="alert">{error}</p>}
      <button type="submit" className="nav-button" disabled={saving}>
        {saving ? "Saving…" : "Update status"}
      </button>
    </form>
  );
}
