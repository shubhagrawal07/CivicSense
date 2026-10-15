import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useReportPolling } from "./useReportPolling";
import { getReport } from "../api/reports";
import type { Report } from "../api/types";

vi.mock("../api/reports", () => ({
  getReport: vi.fn(),
}));

function makeReport(overrides: Partial<Report>): Report {
  return {
    id: "1",
    latitude: 0,
    longitude: 0,
    processing_status: "PENDING",
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// Fake timers are used throughout, so timer advances are driven explicitly
// via vi.advanceTimersByTimeAsync rather than @testing-library's `waitFor`
// (which polls on real timers and would hang forever here).
describe("useReportPolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("stops polling once the report is DONE", async () => {
    (getReport as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeReport({ processing_status: "DONE" }),
    );

    const { result } = renderHook(() => useReportPolling("1"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.report?.processing_status).toBe("DONE");
    expect(result.current.isLoading).toBe(false);

    const callsAfterDone = (getReport as ReturnType<typeof vi.fn>).mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect((getReport as ReturnType<typeof vi.fn>).mock.calls.length).toBe(
      callsAfterDone,
    );
  });

  it("stops polling once the report is FAILED", async () => {
    (getReport as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeReport({ processing_status: "FAILED", error: "boom" }),
    );

    const { result } = renderHook(() => useReportPolling("1"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.report?.processing_status).toBe("FAILED");
    expect(result.current.report?.error).toBe("boom");
  });

  it("flips timedOut after ~2 minutes of PENDING/PROCESSING", async () => {
    (getReport as ReturnType<typeof vi.fn>).mockResolvedValue(
      makeReport({ processing_status: "PROCESSING" }),
    );

    const { result } = renderHook(() => useReportPolling("1"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.isLoading).toBe(false);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000 + 5000);
    });

    expect(result.current.timedOut).toBe(true);
  });
});
