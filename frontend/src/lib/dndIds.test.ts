import { dndActiveToCardId, dndCardId, dndColumnId, dndOverToDragOver } from "@/lib/dndIds";

describe("dndIds", () => {
  it("builds unique column vs card ids", () => {
    expect(dndColumnId("5")).toBe("col-5");
    expect(dndCardId("5")).toBe("card-5");
    expect(dndColumnId("5")).not.toBe(dndCardId("5"));
  });

  it("parses drag-over payloads", () => {
    expect(dndOverToDragOver("col-12")).toEqual({
      type: "column",
      columnId: "12",
    });
    expect(dndOverToDragOver("card-12")).toEqual({
      type: "card",
      cardId: "12",
    });
  });

  it("strips card prefix from active id", () => {
    expect(dndActiveToCardId("card-99")).toBe("99");
    expect(dndActiveToCardId("legacy")).toBe("legacy");
  });
});
