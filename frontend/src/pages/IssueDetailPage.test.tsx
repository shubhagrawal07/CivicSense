import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Issue } from "../api/types";
import { IssueDetailPage } from "./IssueDetailPage";

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map">{children}</div>
  ),
  TileLayer: () => null,
  Marker: () => null,
}));

const stub = vi.hoisted(() => ({
  calls: 0,
  load: (() => new Promise(() => {})) as (id: string) => Promise<unknown>,
}));

vi.mock("../api/issues", () => ({
  getIssue: (id: string) => {
    stub.calls += 1;
    return stub.load(id);
  },
}));

const issue: Issue = {
  id: 7,
  category: "pothole",
  severity: "HIGH",
  status: "IN_PROGRESS",
  location: { lat: 19.1, lng: 72.9 },
  report_count: 3,
  first_reported_at: "2026-10-01T10:00:00Z",
  last_reported_at: "2026-10-05T10:00:00Z",
  department: { id: 1, name: "Roads" },
  authority: { id: 2, name: "City Corporation", jurisdiction: "Mumbai" },
  contacts: [
    {
      type: "HELPLINE",
      value: "1916",
      source_url: "https://example.org/contacts",
      last_verified_at: "2026-09-01",
      verified: true,
    },
    {
      type: "EMAIL",
      value: "help@example.org",
      source_url: null,
      last_verified_at: null,
      verified: false,
    },
  ],
  status_history: [
    { status: "IN_PROGRESS", changed_at: "2026-10-04T10:00:00Z", note: "On site" },
    { status: "NEW", changed_at: "2026-10-01T10:00:00Z", note: null },
  ],
};

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/issues/:id" element={<IssueDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("IssueDetailPage", () => {
  beforeEach(() => {
    stub.calls = 0;
  });

  it("shows the issue, its history in order and contact sources", async () => {
    stub.load = () => Promise.resolve(issue);
    renderAt("/issues/7");

    expect(await screen.findByText("Issue #7")).toBeInTheDocument();
    expect(screen.getByText("City Corporation (Mumbai)")).toBeInTheDocument();
    expect(screen.getByText("(unverified)")).toBeInTheDocument();
    expect(screen.getByText("https://example.org/contacts")).toBeInTheDocument();

    const steps = screen.getAllByRole("listitem").map((li) => li.textContent);
    const newAt = steps.findIndex((t) => t?.startsWith("New"));
    const progressAt = steps.findIndex((t) => t?.startsWith("In progress"));
    expect(newAt).toBeLessThan(progressAt);
  });

  it("shows a friendly page for a 404", async () => {
    stub.load = () => Promise.reject({ status: 404 });
    renderAt("/issues/99");
    expect(await screen.findByText("Issue not found")).toBeInTheDocument();
  });

  it("does not call the api for a non-numeric id", async () => {
    renderAt("/issues/abc");
    expect(await screen.findByText("Issue not found")).toBeInTheDocument();
    expect(stub.calls).toBe(0);
  });

  it("shows an error banner when the request fails", async () => {
    stub.load = () => Promise.reject(new Error("boom"));
    renderAt("/issues/7");
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
