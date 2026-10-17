import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReportForm } from "./ReportForm";
import { submitReport } from "../../api/reports";

// Leaflet doesn't render meaningfully in jsdom; swap LocationPicker for a
// minimal stub that lets tests set a location without exercising the map.
vi.mock("./LocationPicker", () => ({
  LocationPicker: ({
    onChange,
  }: {
    onChange: (value: { lat: number; lng: number }) => void;
  }) => (
    <button type="button" onClick={() => onChange({ lat: 1, lng: 2 })}>
      Set location
    </button>
  ),
}));

vi.mock("../../api/reports", () => ({
  submitReport: vi.fn(),
}));

describe("ReportForm", () => {
  it("blocks submit when there is no description and no photo", async () => {
    render(<ReportForm onSubmitted={vi.fn()} />);

    await userEvent.click(screen.getByText("Set location"));
    await userEvent.click(screen.getByRole("button", { name: /submit report/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      /description, a photo, or both/i,
    );
    expect(submitReport).not.toHaveBeenCalled();
  });

  it("submits with a description only", async () => {
    const onSubmitted = vi.fn();
    (submitReport as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: "42",
      processing_status: "PENDING",
      created_at: new Date().toISOString(),
    });

    render(<ReportForm onSubmitted={onSubmitted} />);

    await userEvent.type(
      screen.getByLabelText(/description/i),
      "Pothole on Main St",
    );
    await userEvent.click(screen.getByText("Set location"));
    await userEvent.click(screen.getByRole("button", { name: /submit report/i }));

    expect(onSubmitted).toHaveBeenCalledWith("42");
  });

  it("shows a server-side field error", async () => {
    (submitReport as ReturnType<typeof vi.fn>).mockRejectedValue({
      status: 422,
      errors: [{ field: "description", message: "Too long." }],
    });

    render(<ReportForm onSubmitted={vi.fn()} />);

    await userEvent.type(screen.getByLabelText(/description/i), "x".repeat(10));
    await userEvent.click(screen.getByText("Set location"));
    await userEvent.click(screen.getByRole("button", { name: /submit report/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/Too long/);
  });
});
