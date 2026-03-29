import type { BoardData } from "@/lib/kanban";

/**
 * Component tests use numeric string ids so they match the real API shape
 * (`Number(columnId)` / `Number(cardId)` in handlers).
 */
export const testBoardData: BoardData = {
  columns: [
    { id: "1", title: "Backlog", cardIds: ["101", "102"] },
    { id: "2", title: "Discovery", cardIds: ["103"] },
    {
      id: "3",
      title: "In Progress",
      cardIds: ["104", "105"],
    },
    { id: "4", title: "Review", cardIds: ["106"] },
    { id: "5", title: "Done", cardIds: ["107", "108"] },
  ],
  cards: {
    "101": {
      id: "101",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "102": {
      id: "102",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "103": {
      id: "103",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "104": {
      id: "104",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "105": {
      id: "105",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "106": {
      id: "106",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "107": {
      id: "107",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "108": {
      id: "108",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
};
