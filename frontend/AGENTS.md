# Frontend - Agent Reference

## Overview

A Next.js 15 (App Router) single-page Kanban board. Pure frontend demo with no backend, no auth, no persistence. State lives entirely in React component memory.

## Stack

- **Next.js 15** with App Router (`src/app/`)
- **React 19** with hooks only (no state library)
- **TypeScript 5**
- **Tailwind CSS 4** via `@tailwindcss/postcss`
- **dnd-kit** (`@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`) for drag and drop
- **Vitest 3** + Testing Library for unit tests
- **Playwright 1.58** for E2E tests

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           Root layout; loads Space Grotesk + Manrope fonts
│   │   ├── page.tsx             Single route (/); renders <KanbanBoard />
│   │   └── globals.css          CSS custom properties (colors, surfaces, shadows)
│   ├── components/
│   │   ├── KanbanBoard.tsx      Top-level board; owns all state; drag/drop context
│   │   ├── KanbanColumn.tsx     Droppable column; renders its cards + NewCardForm
│   │   ├── KanbanCard.tsx       Draggable card; shows title/details + delete button
│   │   ├── KanbanCardPreview.tsx Card ghost shown in DragOverlay during drag
│   │   └── NewCardForm.tsx      Collapsible add-card form within a column
│   └── lib/
│       ├── kanban.ts            Core types (Card, Column, BoardData) + pure functions
│       │                        + hardcoded initialData (5 columns, 8 cards)
│       └── kanban.test.ts       Unit tests for pure functions in kanban.ts
├── tests/
│   └── kanban.spec.ts           Playwright E2E: page load, add card, drag card
├── src/components/KanbanBoard.test.tsx  Component tests
├── vitest.config.ts             jsdom, global test globals, coverage
├── playwright.config.ts         Chromium only, baseURL http://127.0.0.1:3000
└── package.json
```

## Core Data Model

```typescript
// src/lib/kanban.ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

Cards are stored in a flat lookup map (`Record<string, Card>`). Columns hold ordered arrays of card IDs. This avoids data duplication and makes reordering efficient.

## State Management

All state lives in `KanbanBoard` via a single `useState<BoardData>`. No Redux, Zustand, or Context. Mutations return new board objects (immutable updates with spread). Key handlers:

- `handleRenameColumn(columnId, newTitle)`
- `handleAddCard(columnId, { title, details })`
- `handleDeleteCard(cardId)`
- `handleDragEnd(event)` — calls `moveCard()` from `kanban.ts`

## Drag and Drop

- `DndContext` wraps the whole board with `PointerSensor` (6px activation distance)
- Collision detection: `closestCorners`
- Droppable targets: both column IDs and card IDs
- `moveCard()` in `kanban.ts` handles same-column reorder and cross-column move
- `DragOverlay` renders `<KanbanCardPreview>` while dragging

## CSS / Design Tokens

Custom properties defined in `globals.css` and used throughout:

| Variable | Value | Use |
|---|---|---|
| `--accent-yellow` | `#ecad0a` | Highlights, borders, rings |
| `--primary-blue` | `#209dd7` | Links, key sections |
| `--secondary-purple` | `#753991` | Submit buttons |
| `--navy-dark` | `#032147` | Main headings |
| `--gray-text` | `#888888` | Labels, supporting text |

## Running Locally

```bash
cd frontend
npm install
npm run dev        # dev server on :3000
npm run build      # static export (output: .next/)
npm run test:unit  # vitest
npm run test:e2e   # playwright (requires dev server running)
npm run test:all   # both
```

## What Does NOT Exist (to be built)

- Authentication / login screen
- Backend API calls (fetch/axios)
- Session handling or JWT
- AI chat sidebar
- Data persistence (everything resets on reload)
- Docker build configuration

## Integration Notes for Future Parts

- When adding auth (Part 4): wrap `page.tsx` to redirect unauthenticated users to a `/login` route. No changes needed in the Kanban components themselves.
- When connecting to backend (Part 7): replace `initialData` usage in `KanbanBoard.tsx` with an API fetch. Add optimistic updates or loading state as needed.
- When adding AI sidebar (Part 10): add a sidebar component alongside `<KanbanBoard>` in `page.tsx`. The sidebar will call a backend `/api/chat` endpoint and trigger board state refresh on Kanban updates returned from AI.
