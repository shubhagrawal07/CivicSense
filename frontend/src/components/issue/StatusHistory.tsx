import type { IssueStatusChange } from "../../api/types";
import { issueStatusLabel } from "../report/StatusBadge";

export function StatusHistory({ changes }: { changes: IssueStatusChange[] }) {
  if (changes.length === 0) {
    return <p>No status changes recorded.</p>;
  }

  const oldestFirst = [...changes].sort(
    (a, b) => new Date(a.changed_at).getTime() - new Date(b.changed_at).getTime(),
  );

  return (
    <ol>
      {oldestFirst.map((change, index) => (
        <li key={index}>
          <strong>{issueStatusLabel(change.status)}</strong>
          {" — "}
          {new Date(change.changed_at).toLocaleString()}
          {change.note && <div>{change.note}</div>}
        </li>
      ))}
    </ol>
  );
}
