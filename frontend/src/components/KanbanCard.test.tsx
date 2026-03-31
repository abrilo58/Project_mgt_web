import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanCard } from "@/components/KanbanCard";
import { describe, expect, it, vi } from "vitest";

// Mock dnd-kit sortable since we test drag behavior via E2E
vi.mock("@dnd-kit/sortable", () => ({
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));

vi.mock("@dnd-kit/utilities", () => ({
  CSS: { Transform: { toString: () => undefined } },
}));

const card = { id: "1", title: "Test Card", details: "Some details" };

describe("KanbanCard", () => {
  it("renders title and details", () => {
    render(<KanbanCard card={card} onDelete={vi.fn()} />);
    expect(screen.getByText("Test Card")).toBeInTheDocument();
    expect(screen.getByText("Some details")).toBeInTheDocument();
  });

  it("calls onDelete with card id after confirmation", async () => {
    const onDelete = vi.fn();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<KanbanCard card={card} onDelete={onDelete} />);
    await userEvent.click(
      screen.getByRole("button", { name: /delete test card/i })
    );
    expect(onDelete).toHaveBeenCalledWith("1");
  });

  it("does not call onDelete when confirmation is cancelled", async () => {
    const onDelete = vi.fn();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<KanbanCard card={card} onDelete={onDelete} />);
    await userEvent.click(
      screen.getByRole("button", { name: /delete test card/i })
    );
    expect(onDelete).not.toHaveBeenCalled();
  });

  it("has an accessible delete button label", () => {
    render(<KanbanCard card={card} onDelete={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /delete test card/i })
    ).toBeInTheDocument();
  });
});
