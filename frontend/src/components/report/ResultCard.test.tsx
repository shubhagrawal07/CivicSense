import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Report } from "../../api/types";
import { ResultCard } from "./ResultCard";

const base: Report = {
  id: "12",
  latitude: 19.13,
  longitude: 72.91,
  processing_status: "DONE",
  classification: "pothole",
  classification_source: "BOTH",
  conflict: false,
  predicted_severity: "HIGH",
  department: null,
  issue: null,
  created_at: "2026-11-12T10:00:00Z",
};

function renderCard(report: Report) {
  render(
    <MemoryRouter>
      <ResultCard report={report} />
    </MemoryRouter>,
  );
}

describe("ResultCard", () => {
  it("shows the department name when the backend resolved one", () => {
    renderCard({
      ...base,
      department: { id: 1, name: "Roads and Infrastructure" },
    });

    expect(screen.getByText("Roads and Infrastructure")).toBeInTheDocument();
  });

  it("falls back when no department was resolved", () => {
    renderCard(base);

    expect(screen.getAllByText("Not yet available")).toHaveLength(1);
  });
});
