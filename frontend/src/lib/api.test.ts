import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  boardFromApi,
  createCard,
  deleteCard,
  fetchBoard,
  persistCardMove,
  sendChat,
  updateColumn,
  type ApiBoard,
} from "@/lib/api";

describe("boardFromApi", () => {
  it("maps API payload to BoardData with string ids and sort order", () => {
    const api: ApiBoard = {
      id: 1,
      name: "Kanban Studio",
      columns: [
        {
          id: 2,
          title: "B",
          position: 1,
          cards: [
            { id: 20, title: "c2", details: "d2", position: 1 },
            { id: 10, title: "c1", details: "d1", position: 0 },
          ],
        },
        {
          id: 1,
          title: "A",
          position: 0,
          cards: [],
        },
      ],
    };
    const board = boardFromApi(api);
    expect(board.columns.map((c) => c.id)).toEqual(["1", "2"]);
    expect(board.columns[0].title).toBe("A");
    expect(board.columns[1].cardIds).toEqual(["10", "20"]);
    expect(board.cards["10"].title).toBe("c1");
  });
});

describe("api fetch helpers", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("fetchBoard GETs /api/board and returns mapped data", async () => {
    const payload: ApiBoard = {
      id: 1,
      name: "Kanban Studio",
      columns: [
        {
          id: 1,
          title: "Backlog",
          position: 0,
          cards: [],
        },
      ],
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => payload,
    });
    const board = await fetchBoard();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({ credentials: "include" })
    );
    expect(board.columns).toHaveLength(1);
    expect(board.columns[0].id).toBe("1");
  });

  it("401 triggers redirect to login and throws", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", {
      ...window.location,
      assign,
    });
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
    });
    await expect(fetchBoard()).rejects.toThrow("Unauthorized");
    expect(assign).toHaveBeenCalledWith("/login");
    vi.unstubAllGlobals();
  });

  it("updateColumn PUTs title", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    await updateColumn(3, "Done");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/columns/3",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ title: "Done" }),
      })
    );
  });

  it("createCard POSTs body", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: 5,
        column_id: 1,
        title: "t",
        details: "",
        position: 0,
      }),
    });
    const row = await createCard(1, "t", "");
    expect(row.id).toBe(5);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/cards",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          column_id: 1,
          title: "t",
          details: "",
        }),
      })
    );
  });

  it("deleteCard sends DELETE", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 204 });
    await deleteCard(9);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/cards/9",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("persistCardMove sends PUT with column and position", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    await persistCardMove(7, 2, 0);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/cards/7/move",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ column_id: 2, position: 0 }),
      })
    );
  });

  it("sendChat POSTs message and history", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: "Hi", board_updated: false }),
    });
    const hist = [{ role: "user" as const, content: "yo" }];
    const out = await sendChat("next", hist);
    expect(out).toEqual({ message: "Hi", board_updated: false });
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: "next", history: hist }),
      })
    );
  });

  it("sendChat throws with detail string on error", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "no key" }),
    });
    await expect(sendChat("x", [])).rejects.toThrow("no key");
  });
});
