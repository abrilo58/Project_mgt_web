import { moveCard, type Column } from "@/lib/kanban";

describe("moveCard", () => {
  const baseColumns: Column[] = [
    { id: "col-a", title: "A", cardIds: ["card-1", "card-2"] },
    { id: "col-b", title: "B", cardIds: ["card-3"] },
  ];

  it("reorders cards in the same column", () => {
    const result = moveCard(baseColumns, "card-2", {
      type: "card",
      cardId: "card-1",
    });
    expect(result[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("moves cards to another column", () => {
    const result = moveCard(baseColumns, "card-2", {
      type: "card",
      cardId: "card-3",
    });
    expect(result[0].cardIds).toEqual(["card-1"]);
    expect(result[1].cardIds).toEqual(["card-2", "card-3"]);
  });

  it("drops cards to the end of a column", () => {
    const result = moveCard(baseColumns, "card-1", {
      type: "column",
      columnId: "col-b",
    });
    expect(result[0].cardIds).toEqual(["card-2"]);
    expect(result[1].cardIds).toEqual(["card-3", "card-1"]);
  });

  it("preserves unrelated columns when moving a card between two others", () => {
    const threeColumns: Column[] = [
      { id: "col-a", title: "A", cardIds: ["card-1"] },
      { id: "col-b", title: "B", cardIds: ["card-2"] },
      { id: "col-c", title: "C", cardIds: ["card-3"] },
    ];
    const result = moveCard(threeColumns, "card-1", {
      type: "column",
      columnId: "col-b",
    });
    expect(result[0].cardIds).toEqual([]);
    expect(result[1].cardIds).toEqual(["card-2", "card-1"]);
    expect(result[2].cardIds).toEqual(["card-3"]);
  });

  it("returns columns unchanged when active id is not a card in any column", () => {
    const result = moveCard(baseColumns, "col-a", {
      type: "column",
      columnId: "col-b",
    });
    expect(result).toBe(baseColumns);
  });

  it("returns columns unchanged when active and over ids are unknown", () => {
    const result = moveCard(baseColumns, "unknown", {
      type: "column",
      columnId: "col-b",
    });
    expect(result).toBe(baseColumns);
  });

  it("returns columns unchanged when moving card to same position", () => {
    const result = moveCard(baseColumns, "card-1", {
      type: "card",
      cardId: "card-1",
    });
    expect(result).toBe(baseColumns);
  });

  it("resolves source column by card even when a column shares the same id", () => {
    const columns: Column[] = [
      { id: "1", title: "First", cardIds: ["10"] },
      { id: "2", title: "Second", cardIds: ["1"] },
    ];
    const result = moveCard(columns, "1", { type: "column", columnId: "1" });
    expect(result[0].cardIds).toEqual(["10", "1"]);
    expect(result[1].cardIds).toEqual([]);
  });
});
