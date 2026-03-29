import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { sendChat } from "@/lib/api";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", async (importOriginal) => {
  const mod = await importOriginal<typeof import("@/lib/api")>();
  return { ...mod, sendChat: vi.fn() };
});

describe("AIChatSidebar", () => {
  beforeEach(() => {
    vi.mocked(sendChat).mockResolvedValue({
      message: "Hello back",
      board_updated: false,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty chat state when open", async () => {
    render(<AIChatSidebar />);
    await userEvent.click(screen.getByTestId("ai-chat-toggle"));
    expect(
      screen.getByText(/No messages yet/i)
    ).toBeInTheDocument();
  });

  it("submits a message and shows user + assistant in the list", async () => {
    render(<AIChatSidebar />);
    await userEvent.click(screen.getByTestId("ai-chat-toggle"));
    await userEvent.type(screen.getByTestId("ai-chat-input"), "Hi there");
    await userEvent.click(screen.getByTestId("ai-chat-send"));
    await waitFor(() => {
      expect(sendChat).toHaveBeenCalledWith("Hi there", []);
    });
    expect(screen.getByText("Hi there")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Hello back")).toBeInTheDocument();
    });
  });

  it("shows loading state while awaiting response", async () => {
    let resolveFn: (v: { message: string; board_updated: boolean }) => void =
      () => {};
    const pending = new Promise<{ message: string; board_updated: boolean }>(
      (r) => {
        resolveFn = r;
      }
    );
    vi.mocked(sendChat).mockReturnValue(pending);

    render(<AIChatSidebar />);
    await userEvent.click(screen.getByTestId("ai-chat-toggle"));
    await userEvent.type(screen.getByTestId("ai-chat-input"), "Wait");
    await userEvent.click(screen.getByTestId("ai-chat-send"));

    expect(screen.getByTestId("ai-chat-loading")).toBeInTheDocument();
    resolveFn({ message: "Done", board_updated: false });
    await waitFor(() => {
      expect(screen.queryByTestId("ai-chat-loading")).not.toBeInTheDocument();
    });
  });

  it("calls onBoardUpdate when board_updated is true", async () => {
    vi.mocked(sendChat).mockResolvedValue({
      message: "Updated",
      board_updated: true,
    });
    const onBoardUpdate = vi.fn();
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByTestId("ai-chat-toggle"));
    await userEvent.type(screen.getByTestId("ai-chat-input"), "Add a card");
    await userEvent.click(screen.getByTestId("ai-chat-send"));
    await waitFor(() => {
      expect(onBoardUpdate).toHaveBeenCalled();
    });
  });

  it("passes prior messages as history on the second send", async () => {
    render(<AIChatSidebar />);
    await userEvent.click(screen.getByTestId("ai-chat-toggle"));
    await userEvent.type(screen.getByTestId("ai-chat-input"), "One");
    await userEvent.click(screen.getByTestId("ai-chat-send"));
    await waitFor(() => expect(screen.getByText("Hello back")).toBeInTheDocument());

    await userEvent.type(screen.getByTestId("ai-chat-input"), "Two");
    await userEvent.click(screen.getByTestId("ai-chat-send"));
    await waitFor(() => {
      expect(sendChat).toHaveBeenLastCalledWith("Two", [
        { role: "user", content: "One" },
        { role: "assistant", content: "Hello back" },
      ]);
    });
  });
});
