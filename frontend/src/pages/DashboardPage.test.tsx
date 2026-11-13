import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { StatsSummary } from "../api/types";
import { DashboardPage } from "./DashboardPage";

const stub = vi.hoisted(() => ({
  load: (() => new Promise(() => {})) as () => Promise<unknown>,
}));

vi.mock("../api/stats", () => ({
  getSummary: () => stub.load(),
  getBreakdown: () => new Promise(() => {}),
}));

const summary: StatsSummary = {
  total: 30,
  open: 12,
  in_progress: 8,
  resolved: 9,
  avg_resolution_days: 4.5,
};

describe("DashboardPage", () => {
  beforeEach(() => {
    stub.load = () => new Promise(() => {});
  });

  it("shows a loading message first", () => {
    render(<DashboardPage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows the numbers the api returned", async () => {
    stub.load = () => Promise.resolve(summary);
    render(<DashboardPage />);

    expect(await screen.findByText("30")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
  });

  it("shows N/A when nothing has been resolved", async () => {
    stub.load = () =>
      Promise.resolve({ ...summary, resolved: 0, avg_resolution_days: null });
    render(<DashboardPage />);
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("puts the charts section below the cards", async () => {
    stub.load = () => Promise.resolve(summary);
    render(<DashboardPage />);

    await screen.findByText("30");
    expect(screen.getByText("Loading charts…")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    stub.load = () => Promise.reject(new Error("boom"));
    render(<DashboardPage />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
