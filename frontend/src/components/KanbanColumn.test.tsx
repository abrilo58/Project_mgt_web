import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanColumn } from "@/components/KanbanColumn";
import { describe, expect, it, vi } from "vitest";

// Mock dnd-kit hooks
vi.mock("@dnd-kit/core", () => ({
  useDroppable: () => ({ setNodeRef: vi.fn(), isOver: false }),
}));

vi.mock("@dnd-kit/sortable", () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  verticalListSortingStrategy: {},
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

const column = { id: "1", title: "Backlog", cardIds: ["101", "102"] };
const cards = [
  { id: "101", title: "Card A", details: "Details A" },
  { id: "102", title: "Card B", details: "Details B" },
];

describe("KanbanColumn", () => {
  it("renders column title and card count", () => {
    render(
      <KanbanColumn
        column={column}
        cards={cards}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByDisplayValue("Backlog")).toBeInTheDocument();
    expect(screen.getByText("2 cards")).toBeInTheDocument();
  });

  it("renders all cards", () => {
    render(
      <KanbanColumn
        column={column}
        cards={cards}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByText("Card A")).toBeInTheDocument();
    expect(screen.getByText("Card B")).toBeInTheDocument();
  });

  it("calls onRename when title is changed and blurred", async () => {
    const onRename = vi.fn();
    render(
      <KanbanColumn
        column={column}
        cards={cards}
        onRename={onRename}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    const input = screen.getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Title");
    await userEvent.tab();
    expect(onRename).toHaveBeenCalledWith("1", "New Title");
  });

  it("reverts to original title when input is cleared and blurred", async () => {
    render(
      <KanbanColumn
        column={column}
        cards={cards}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    const input = screen.getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.tab();
    expect(input).toHaveValue("Backlog");
  });

  it("shows empty state when no cards", () => {
    render(
      <KanbanColumn
        column={{ id: "1", title: "Empty", cardIds: [] }}
        cards={[]}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByText(/drop a card here/i)).toBeInTheDocument();
  });
});
