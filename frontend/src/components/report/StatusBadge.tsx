import type { IssueStatus, ProcessingStatus } from "../../api/types";
import { statusBadgeLabel } from "./statusLabels";

interface StatusBadgeProps {
  processingStatus: ProcessingStatus;
  issueStatus?: IssueStatus | null;
}

export function StatusBadge({ processingStatus, issueStatus }: StatusBadgeProps) {
  return <span>{statusBadgeLabel(processingStatus, issueStatus)}</span>;
}
