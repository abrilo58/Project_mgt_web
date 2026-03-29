import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import {
  createCard,
  deleteCard,
  fetchBoard,
  persistCardMove,
  updateColumn,
} from "@/lib/api";
import { testBoardData } from "@/test/fixtures/board";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({
  fetchBoard: vi.fn(),
  updateColumn: vi.fn(),
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  persistCardMove: vi.fn(),
}));

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.mocked(fetchBoard).mockResolvedValue(testBoardData);
    vi.mocked(updateColumn).mockResolvedValue(undefined);
    vi.mocked(createCard).mockResolvedValue({
      id: 199,
      column_id: 1,
      title: "New card",
      details: "Notes",
      position: 2,
    });
    vi.mocked(deleteCard).mockResolvedValue(undefined);
    vi.mocked(persistCardMove).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders five columns after load", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
    expect(fetchBoard).toHaveBeenCalled();
  });

  it("shows load error and retry loads the board", async () => {
    vi.mocked(fetchBoard)
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce(testBoardData);
    render(<KanbanBoard />);
    await waitFor(() =>
      expect(screen.getByText(/network down/i)).toBeInTheDocument()
    );
    await userEvent.click(screen.getByRole("button", { name: /^retry$/i }));
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
  });

  it("renames a column on blur and calls updateColumn", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();
    await waitFor(() => {
      expect(updateColumn).toHaveBeenCalledWith(1, "New Name");
    });
  });

  it("shows empty column placeholder when all cards are deleted", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const discoveryColumn = screen.getByTestId("column-2");
    const deleteButton = within(discoveryColumn).getByRole("button", {
      name: /delete prototype analytics view/i,
    });
    await userEvent.click(deleteButton);
    await waitFor(() => {
      expect(deleteCard).toHaveBeenCalledWith(103);
    });
    expect(within(discoveryColumn).getByText(/drop a card here/i)).toBeInTheDocument();
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(
      within(column).getByRole("button", { name: /add card/i })
    );

    await waitFor(() => {
      expect(createCard).toHaveBeenCalledWith(1, "New card", "Notes");
    });
    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(deleteCard).toHaveBeenCalledWith(199);
    });
    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });
});
