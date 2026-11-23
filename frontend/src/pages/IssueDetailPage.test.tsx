import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  role: "CITIZEN",
  update: vi.fn(),
  calls: 0,
  load: (() => new Promise(() => {})) as (id: string) => Promise<unknown>,
}));

vi.mock("../api/issues", () => ({
  getIssue: (id: string) => {
    stub.calls += 1;
    return stub.load(id);
  },
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, name: "Tester", role: stub.role } }),
}));

vi.mock("../api/admin", () => ({
  updateIssueStatus: (...args: unknown[]) => stub.update(...args),
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
    stub.role = "CITIZEN";
    stub.update.mockReset();
    stub.update.mockResolvedValue(undefined);
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

  it("lets an admin change the status, and hides the form from citizens", async () => {
    stub.load = () => Promise.resolve(issue);
    renderAt("/issues/7");
    await screen.findByText("Issue #7");
    expect(screen.queryByText("Update status")).not.toBeInTheDocument();

    stub.role = "ADMIN";
    renderAt("/issues/7");
    const select = await screen.findByLabelText("New status");
    fireEvent.change(select, { target: { value: "RESOLVED" } });
    fireEvent.click(screen.getByRole("button", { name: "Update status" }));

    await waitFor(() => expect(stub.update).toHaveBeenCalledWith(7, "RESOLVED", ""));
  });
});
