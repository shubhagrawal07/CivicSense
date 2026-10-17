import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ImageUpload } from "./ImageUpload";

function makeFile(name: string, type: string, sizeBytes: number): File {
  const file = new File(["x"], name, { type });
  Object.defineProperty(file, "size", { value: sizeBytes });
  return file;
}

describe("ImageUpload", () => {
  it("rejects a file with an unsupported type", async () => {
    const onChange = vi.fn();
    render(<ImageUpload onChange={onChange} />);
    const input = screen.getByLabelText(/photo/i);

    // user-event normally skips files that don't match the input's `accept`
    // attribute (never firing change) — disable that here since we're
    // testing our own rejection logic, not the browser's file picker filter.
    await userEvent.upload(input, makeFile("scan.pdf", "application/pdf", 1000), {
      applyAccept: false,
    });

    expect(screen.getByRole("alert")).toHaveTextContent(/JPEG or PNG/i);
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("rejects a file over 5MB", async () => {
    const onChange = vi.fn();
    render(<ImageUpload onChange={onChange} />);
    const input = screen.getByLabelText(/photo/i);

    await userEvent.upload(
      input,
      makeFile("big.png", "image/png", 6 * 1024 * 1024),
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/5MB/i);
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("accepts a valid image", async () => {
    const onChange = vi.fn();
    render(<ImageUpload onChange={onChange} />);
    const input = screen.getByLabelText(/photo/i);
    const file = makeFile("pothole.png", "image/png", 1000);

    await userEvent.upload(input, file);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(onChange).toHaveBeenCalledWith(file);
  });
});
