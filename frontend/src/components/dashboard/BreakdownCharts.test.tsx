import { cloneElement, type ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { StatsBreakdown } from "../../api/types";
import { BreakdownCharts } from "./BreakdownCharts";

const stub = vi.hoisted(() => ({
  load: (() => new Promise(() => {})) as () => Promise<unknown>,
}));

vi.mock("../../api/stats", () => ({
  getBreakdown: () => stub.load(),
}));

// jsdom has no layout, so the responsive wrapper would render nothing
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children, { width: 600, height: 300 }),
  };
});

const data: StatsBreakdown = {
  by_category: [
    { category: "pothole", count: 14 },
    { category: "garbage", count: 9 },
  ],
  by_severity: [
    { severity: "HIGH", count: 15 },
    { severity: "LOW", count: 7 },
  ],
};

describe("BreakdownCharts", () => {
  beforeEach(() => {
    stub.load = () => new Promise(() => {});
  });

  it("shows a loading message first", () => {
    render(<BreakdownCharts />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading charts");
  });

  it("draws a bar and a count for every category", async () => {
    stub.load = () => Promise.resolve(data);
    render(<BreakdownCharts />);

    expect(await screen.findByText("Issues by category")).toBeInTheDocument();
    expect(screen.getByText("pothole")).toBeInTheDocument();
    expect(screen.getByText("garbage")).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
  });

  it("lists all four severities in order, with zero for the missing ones", async () => {
    stub.load = () => Promise.resolve(data);
    render(<BreakdownCharts />);

    const heading = await screen.findByText("Issues by severity");
    const box = heading.closest("section") as HTMLElement;
    const ticks = Array.from(
      box.querySelectorAll(".recharts-xAxis .recharts-cartesian-axis-tick-value"),
    ).map((node) => node.textContent);
    expect(ticks).toEqual(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);

    const counts = Array.from(box.querySelectorAll(".recharts-label-list text")).map(
      (node) => node.textContent,
    );
    expect(counts).toContain("15");
    expect(counts).toContain("7");
    expect(counts).toContain("0");
  });

  it("says no data for a chart whose list is empty", async () => {
    stub.load = () => Promise.resolve({ ...data, by_severity: [] } satisfies StatsBreakdown);
    render(<BreakdownCharts />);

    await screen.findByText("Issues by severity");
    expect(screen.getAllByText("No data")).toHaveLength(1);
    expect(screen.getByText("pothole")).toBeInTheDocument();
  });

  it("says no data for both charts when nothing is reported yet", async () => {
    stub.load = () => Promise.resolve({ by_category: [], by_severity: [] });
    render(<BreakdownCharts />);

    await screen.findByText("Issues by category");
    expect(screen.getAllByText("No data")).toHaveLength(2);
  });

  it("shows an error message when the request fails", async () => {
    stub.load = () => Promise.reject(new Error("boom"));
    render(<BreakdownCharts />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
