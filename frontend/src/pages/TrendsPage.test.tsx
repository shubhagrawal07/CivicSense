import { cloneElement, type ReactElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrendPoint } from "../api/types";
import { TrendsPage } from "./TrendsPage";

const stub = vi.hoisted(() => ({
  load: vi.fn<(interval: string, category: string) => Promise<unknown>>(),
}));

vi.mock("../api/stats", () => ({
  getTrend: (interval: string, category: string) => stub.load(interval, category),
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

const points: TrendPoint[] = [
  { period: "2026-10-05", count: 9 },
  { period: "2026-10-12", count: 14 },
];

describe("TrendsPage", () => {
  beforeEach(() => {
    stub.load.mockReset();
    stub.load.mockResolvedValue(points);
  });

  it("shows a loading message, then the chart", async () => {
    render(<TrendsPage />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading trend");
    expect(await screen.findByText("Issues reported per week")).toBeInTheDocument();
    expect(screen.getByText("2026-10-12")).toBeInTheDocument();
  });

  it("starts with the week interval and all categories", async () => {
    render(<TrendsPage />);
    await screen.findByText("Issues reported per week");
    expect(stub.load).toHaveBeenCalledWith("week", "");
    expect(screen.getByRole("button", { name: "Week" })).toHaveAttribute("aria-pressed", "true");
  });

  it("fetches again when the interval changes", async () => {
    render(<TrendsPage />);
    await screen.findByText("Issues reported per week");

    fireEvent.click(screen.getByRole("button", { name: "Day" }));

    expect(await screen.findByText("Issues reported per day")).toBeInTheDocument();
    expect(stub.load).toHaveBeenLastCalledWith("day", "");
  });

  it("fetches again when the category changes", async () => {
    render(<TrendsPage />);
    await screen.findByText("Issues reported per week");

    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "pothole" } });

    await waitFor(() => expect(stub.load).toHaveBeenLastCalledWith("week", "pothole"));
  });

  it("says so when the selection has no data", async () => {
    stub.load.mockResolvedValue([]);
    render(<TrendsPage />);
    expect(await screen.findByText("No data for this selection")).toBeInTheDocument();
    expect(screen.queryByText("Issues reported per week")).not.toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    stub.load.mockRejectedValue(new Error("boom"));
    render(<TrendsPage />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
