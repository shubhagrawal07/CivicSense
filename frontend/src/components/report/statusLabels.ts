import type { IssueStatus, ProcessingStatus } from "../../api/types";

export const ISSUE_STATUS_LABEL: Record<IssueStatus, string> = {
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
