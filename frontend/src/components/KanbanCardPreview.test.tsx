import { render, screen } from "@testing-library/react";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";

const card = { id: "1", title: "Test card", details: "Some details" };

describe("KanbanCardPreview", () => {
  it("renders card title and details", () => {
    render(<KanbanCardPreview card={card} />);
    expect(screen.getByText("Test card")).toBeInTheDocument();
    expect(screen.getByText("Some details")).toBeInTheDocument();
  });

  it("renders without details text when details is empty", () => {
    render(<KanbanCardPreview card={{ ...card, details: "" }} />);
    expect(screen.getByText("Test card")).toBeInTheDocument();
  });
});
