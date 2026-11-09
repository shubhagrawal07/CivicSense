import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { DataQuality } from "../api/types";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { DataQualityPage } from "./DataQualityPage";

const stub = vi.hoisted(() => ({
  role: "ADMIN",
}));

vi.mock("../api/admin", () => ({
  getDataQuality: () => Promise.resolve(data),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, name: "Test", email: "t@example.com", role: stub.role },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

const data: DataQuality = {
  reports_without_description: 0,
  reports_without_image: 3,
  reports_failed_processing: 0,
  issues_outside_any_ward: null,
  contacts_unverified: 9,
  contacts_older_than_90_days: 0,
};

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/admin/data-quality"]}>
      <Routes>
        <Route path="/" element={<p>home page</p>} />
        <Route
          path="/admin/data-quality"
          element={
            <ProtectedRoute role="ADMIN">
              <DataQualityPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("DataQualityPage", () => {
  it("shows the counts with the right badge colours", async () => {
    stub.role = "ADMIN";
    renderPage();

    expect(await screen.findByText("9")).toHaveClass("badge--orange");
    expect(screen.getByText("3")).toHaveClass("badge--orange");
    expect(screen.getByText("N/A")).toHaveClass("badge--grey");
    expect(screen.getAllByText("0")[0]).toHaveClass("badge--green");
  });

  it("sends a non-admin user to the home page", () => {
    stub.role = "CITIZEN";
    renderPage();

    expect(screen.getByText("home page")).toBeInTheDocument();
  });
});
