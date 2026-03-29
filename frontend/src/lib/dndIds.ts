import type { DragOver } from "@/lib/kanban";

/**
 * Column and card rows can share the same numeric id in SQLite (different tables).
 * dnd-kit requires globally unique drag ids, so we namespace droppables vs sortables.
 */
export const dndColumnId = (columnId: string) => `col-${columnId}`;

export const dndCardId = (cardId: string) => `card-${cardId}`;

export function dndActiveToCardId(id: string): string {
  if (id.startsWith("card-")) {
    return id.slice("card-".length);
  }
  return id;
}

export function dndOverToDragOver(id: string): DragOver {
  if (id.startsWith("col-")) {
    return { type: "column", columnId: id.slice("col-".length) };
  }
  if (id.startsWith("card-")) {
    return { type: "card", cardId: id.slice("card-".length) };
  }
  return { type: "card", cardId: id };
}
