import type { IssueStatus, ProcessingStatus } from "../../api/types";

const ISSUE_STATUS_LABEL: Record<IssueStatus, string> = {
  NEW: "New",
  UNDER_REVIEW: "Under review",
  CLASSIFIED: "Classified",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In progress",
  RESOLVED: "Resolved",
  VERIFIED: "Verified",
  CLOSED: "Closed",
  DUPLICATE: "Duplicate",
  REJECTED: "Rejected",
  ESCALATED: "Escalated",
  REOPENED: "Reopened",
};

export function issueStatusLabel(status: IssueStatus): string {
  return ISSUE_STATUS_LABEL[status];
}

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
  return issueStatus ? issueStatusLabel(issueStatus) : "New";
}

interface StatusBadgeProps {
  processingStatus: ProcessingStatus;
  issueStatus?: IssueStatus | null;
}

export function StatusBadge({ processingStatus, issueStatus }: StatusBadgeProps) {
  return <span>{statusBadgeLabel(processingStatus, issueStatus)}</span>;
}
