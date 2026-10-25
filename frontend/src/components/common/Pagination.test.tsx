import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it("disables Previous/Next at the edges", () => {
    const { rerender } = render(
      <Pagination total={50} limit={20} offset={0} onOffsetChange={vi.fn()} />,
    );
    expect(screen.getByText("Previous")).toBeDisabled();
    expect(screen.getByText("Next")).not.toBeDisabled();

    rerender(<Pagination total={50} limit={20} offset={40} onOffsetChange={vi.fn()} />);
    expect(screen.getByText("Next")).toBeDisabled();
    expect(screen.getByText("Previous")).not.toBeDisabled();
  });

  it("calls onOffsetChange with the next and previous offsets", () => {
    const onOffsetChange = vi.fn();
    render(<Pagination total={50} limit={20} offset={20} onOffsetChange={onOffsetChange} />);

    fireEvent.click(screen.getByText("Next"));
    expect(onOffsetChange).toHaveBeenCalledWith(40);

    fireEvent.click(screen.getByText("Previous"));
    expect(onOffsetChange).toHaveBeenCalledWith(0);
  });
});
