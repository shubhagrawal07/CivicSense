import type { IssueStatus, ProcessingStatus } from "../../api/types";

const ISSUE_STATUS_LABEL: Record<IssueStatus, string> = {
  NEW: "New",
  IN_PROGRESS: "In progress",
  RESOLVED: "Resolved",
};

export function statusBadgeLabel(
  processingStatus: ProcessingStatus,
  issueStatus?: IssueStatus | null,
): string {
  if (processingStatus === "PENDING" || processingStatus === "PROCESSING") {
    return "Analysing";
  }
  if (processingStatus === "FAILED") {
    return "Analysis failed";
  }
  return issueStatus ? ISSUE_STATUS_LABEL[issueStatus] : "New";
}

interface StatusBadgeProps {
  processingStatus: ProcessingStatus;
  issueStatus?: IssueStatus | null;
}

export function StatusBadge({ processingStatus, issueStatus }: StatusBadgeProps) {
  return <span>{statusBadgeLabel(processingStatus, issueStatus)}</span>;
}
