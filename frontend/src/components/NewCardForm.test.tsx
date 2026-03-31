import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NewCardForm } from "@/components/NewCardForm";
import { describe, expect, it, vi } from "vitest";

describe("NewCardForm", () => {
  it("shows 'Add a card' button by default", () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /add a card/i })
    ).toBeInTheDocument();
  });

  it("opens form when 'Add a card' is clicked", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(
      screen.getByRole("button", { name: /add a card/i })
    );
    expect(screen.getByPlaceholderText(/card title/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/details/i)).toBeInTheDocument();
  });

  it("calls onAdd with title and details on submit", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    await userEvent.click(
      screen.getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      screen.getByPlaceholderText(/card title/i),
      "My Card"
    );
    await userEvent.type(screen.getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(
      screen.getByRole("button", { name: /^add card$/i })
    );
    expect(onAdd).toHaveBeenCalledWith("My Card", "Notes");
  });

  it("does not call onAdd when title is empty", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    await userEvent.click(
      screen.getByRole("button", { name: /add a card/i })
    );
    await userEvent.click(
      screen.getByRole("button", { name: /^add card$/i })
    );
    expect(onAdd).not.toHaveBeenCalled();
  });

  it("closes form and resets fields on cancel", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(
      screen.getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      screen.getByPlaceholderText(/card title/i),
      "Draft"
    );
    await userEvent.click(
      screen.getByRole("button", { name: /cancel/i })
    );
    // Should go back to the "Add a card" button
    expect(
      screen.getByRole("button", { name: /add a card/i })
    ).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/card title/i)).not.toBeInTheDocument();
  });
});
