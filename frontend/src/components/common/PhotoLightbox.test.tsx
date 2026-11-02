import { fireEvent, render, screen } from "@testing-library/react";
import { PhotoLightbox } from "./PhotoLightbox";

// tests are AI generated

describe("PhotoLightbox", () => {
  it("opens the photo and closes on the close button", () => {
    render(<PhotoLightbox src="/uploads/a.jpg" alt="Uploaded photo" />);
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "View photo" }));
    expect(screen.getByRole("dialog")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("closes when the blurred background is clicked", () => {
    render(<PhotoLightbox src="/uploads/a.jpg" alt="Uploaded photo" />);
    fireEvent.click(screen.getByRole("button", { name: "View photo" }));

    fireEvent.click(screen.getByRole("dialog"));

    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("stays open when the photo itself is clicked", () => {
    render(<PhotoLightbox src="/uploads/a.jpg" alt="Uploaded photo" />);
    fireEvent.click(screen.getByRole("button", { name: "View photo" }));

    fireEvent.click(screen.getAllByAltText("Uploaded photo")[1]);

    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("closes on Escape", () => {
    render(<PhotoLightbox src="/uploads/a.jpg" alt="Uploaded photo" />);
    fireEvent.click(screen.getByRole("button", { name: "View photo" }));

    fireEvent.keyDown(window, { key: "Escape" });

    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
