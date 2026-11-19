import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WardCount } from "../api/types";
import { WardMapPage } from "./WardMapPage";

const stub = vi.hoisted(() => ({
  boundaries: vi.fn(),
  counts: vi.fn<(category: string) => Promise<unknown>>(),
}));

vi.mock("../api/wards", () => ({
  getWardBoundaries: () => stub.boundaries(),
  getWardCounts: (category: string) => stub.counts(category),
}));

vi.mock("../components/map/WardMap", () => ({
  WardMap: ({ counts }: { counts: WardCount[] }) => (
    <p data-testid="map">{counts.map((row) => row.issue_count).join(",")}</p>
  ),
}));

const everything: WardCount[] = [
  { ward_id: 1, ward_name: "A Ward", issue_count: 34, open_count: 12, high_severity_count: 5 },
  { ward_id: 2, ward_name: "B Ward", issue_count: 0, open_count: 0, high_severity_count: 0 },
];
const potholes: WardCount[] = [
  { ward_id: 1, ward_name: "A Ward", issue_count: 6, open_count: 2, high_severity_count: 1 },
  { ward_id: 2, ward_name: "B Ward", issue_count: 0, open_count: 0, high_severity_count: 0 },
];

describe("WardMapPage", () => {
  beforeEach(() => {
    stub.boundaries.mockReset();
    stub.counts.mockReset();
    stub.boundaries.mockResolvedValue({ type: "FeatureCollection", features: [] });
    stub.counts.mockImplementation((category) =>
      Promise.resolve(category === "pothole" ? potholes : everything),
    );
  });

  it("fetches only the counts again when the category changes", async () => {
    render(<WardMapPage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(await screen.findByTestId("map")).toHaveTextContent("34,0");

    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "pothole" } });

    await waitFor(() => expect(screen.getByTestId("map")).toHaveTextContent("6,0"));
    expect(stub.counts).toHaveBeenLastCalledWith("pothole");
    expect(stub.boundaries).toHaveBeenCalledTimes(1);
  });
});
