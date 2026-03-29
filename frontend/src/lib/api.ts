import type { BoardData, Card, Column } from "@/lib/kanban";

export type ApiCard = {
  id: number;
  title: string;
  details: string;
  position: number;
};

export type ApiColumn = {
  id: number;
  title: string;
  position: number;
  cards: ApiCard[];
};

export type ApiBoard = {
  id: number;
  name: string;
  columns: ApiColumn[];
};

function redirectToLogin() {
  if (typeof window !== "undefined") {
    window.location.assign("/login");
  }
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(path, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    redirectToLogin();
    throw new Error("Unauthorized");
  }
  return res;
}

export function boardFromApi(data: ApiBoard): BoardData {
  const cards: Record<string, Card> = {};
  const columns: Column[] = [...data.columns]
    .sort((a, b) => a.position - b.position)
    .map((col) => {
      const cardIds = [...col.cards]
        .sort((a, b) => a.position - b.position)
        .map((c) => {
          const id = String(c.id);
          cards[id] = { id, title: c.title, details: c.details };
          return id;
        });
      return {
        id: String(col.id),
        title: col.title,
        cardIds,
      };
    });
  return { columns, cards };
}

export async function fetchBoard(): Promise<BoardData> {
  const res = await apiFetch("/api/board");
  if (!res.ok) {
    throw new Error(`Board request failed: ${res.status}`);
  }
  const data = (await res.json()) as ApiBoard;
  return boardFromApi(data);
}

export async function updateColumn(columnId: number, title: string): Promise<void> {
  const res = await apiFetch(`/api/columns/${columnId}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    throw new Error(`Rename column failed: ${res.status}`);
  }
}

export type CreatedCard = {
  id: number;
  column_id: number;
  title: string;
  details: string;
  position: number;
};

export async function createCard(
  columnId: number,
  title: string,
  details: string
): Promise<CreatedCard> {
  const res = await apiFetch("/api/cards", {
    method: "POST",
    body: JSON.stringify({
      column_id: columnId,
      title,
      details: details || "",
    }),
  });
  if (!res.ok) {
    throw new Error(`Create card failed: ${res.status}`);
  }
  return res.json() as Promise<CreatedCard>;
}

export async function deleteCard(cardId: number): Promise<void> {
  const res = await apiFetch(`/api/cards/${cardId}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`Delete card failed: ${res.status}`);
  }
}

export async function persistCardMove(
  cardId: number,
  columnId: number,
  position: number
): Promise<void> {
  const res = await apiFetch(`/api/cards/${cardId}/move`, {
    method: "PUT",
    body: JSON.stringify({ column_id: columnId, position }),
  });
  if (!res.ok) {
    throw new Error(`Move card failed: ${res.status}`);
  }
}
