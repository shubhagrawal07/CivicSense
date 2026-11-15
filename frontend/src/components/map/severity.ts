import type { Severity } from "../../api/types";

export const SEVERITY_COLORS: Record<Severity, string> = {
  CRITICAL: "#b71c1c",
  HIGH: "#e65100",
  MEDIUM: "#f9a825",
  LOW: "#2e7d32",
};

export const UNCLASSIFIED_COLOR = "#757575";

export function severityColor(severity: Severity | null): string {
  return severity ? SEVERITY_COLORS[severity] : UNCLASSIFIED_COLOR;
}

export const SEVERITY_LEGEND: { label: string; color: string }[] = [
  { label: "Critical", color: SEVERITY_COLORS.CRITICAL },
  { label: "High", color: SEVERITY_COLORS.HIGH },
  { label: "Medium", color: SEVERITY_COLORS.MEDIUM },
  { label: "Low", color: SEVERITY_COLORS.LOW },
  { label: "Unclassified", color: UNCLASSIFIED_COLOR },
];
