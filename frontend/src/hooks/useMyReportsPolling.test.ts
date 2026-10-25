import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useMyReportsPolling } from "./useMyReportsPolling";
import { getMyReports } from "../api/reports";
import type { MyReportListItem } from "../api/types";

vi.mock("../api/reports", () => ({
  getMyReports: vi.fn(),
}));

function makeItem(overrides: Partial<MyReportListItem>): MyReportListItem {
  return {
    id: "1",
    created_at: new Date().toISOString(),
    processing_status: "PENDING",
    ...overrides,
  };
}

describe("useMyReportsPolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("stops polling once nothing is PENDING or PROCESSING", async () => {
    (getMyReports as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [makeItem({ processing_status: "DONE" })],
      total: 1,
    });

    const { result } = renderHook(() => useMyReportsPolling(20, 0));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.items[0].processing_status).toBe("DONE");

    const callsAfterDone = (getMyReports as ReturnType<typeof vi.fn>).mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect((getMyReports as ReturnType<typeof vi.fn>).mock.calls.length).toBe(
      callsAfterDone,
    );
  });

  it("flips timedOut after ~2 minutes with something still pending", async () => {
    (getMyReports as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [makeItem({ processing_status: "PENDING" })],
      total: 1,
    });

    const { result } = renderHook(() => useMyReportsPolling(20, 0));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000 + 5000);
    });

    expect(result.current.timedOut).toBe(true);
  });

  it("restarts the fetch and timing when offset changes", async () => {
    (getMyReports as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [makeItem({ processing_status: "DONE" })],
      total: 1,
    });

    const { rerender } = renderHook(
      ({ offset }) => useMyReportsPolling(20, offset),
      { initialProps: { offset: 0 } },
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    const callsBeforeChange = (getMyReports as ReturnType<typeof vi.fn>).mock.calls.length;

    rerender({ offset: 20 });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect((getMyReports as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(
      callsBeforeChange,
    );
    expect(
      (getMyReports as ReturnType<typeof vi.fn>).mock.calls.at(-1)?.[0],
    ).toEqual({ limit: 20, offset: 20 });
  });
});
