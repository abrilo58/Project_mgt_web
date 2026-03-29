# Frontend - Agent Reference

## Overview

Next.js App Router Kanban board backed by the FastAPI API (same origin in Docker or local uvicorn). Board data is loaded from `GET /api/board`; mutations call the Part 6 REST routes. Session is an httpOnly cookie (`credentials: "include"` on fetches).

## Stack

- **Next.js 16** with App Router (`src/app/`)
- **React 19** with hooks only (no state library)
- **TypeScript 5**
- **Tailwind CSS 4** via `@tailwindcss/postcss`
- **dnd-kit** for drag and drop
- **Vitest 3** + Testing Library for unit tests
- **Playwright 1.58** for E2E tests

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx             Auth gate; renders <KanbanBoard /> when /api/auth/me ok
│   │   ├── login/page.tsx       Login form (POST /api/auth/login)
│   │   └── ...
│   ├── components/
│   │   ├── KanbanBoard.tsx      Fetches board; wires API to handlers; loading/error UI
│   │   ├── KanbanColumn.tsx     Column title commits on blur (API rename)
│   │   └── ...
│   ├── lib/
│   │   ├── api.ts               Typed fetch helpers; 401 -> /login
│   │   └── kanban.ts            Types, moveCard(); no initialData (fixtures in tests)
│   └── test/fixtures/board.ts   testBoardData for component tests
├── tests/kanban.spec.ts         Playwright (serial); targets backend (see below)
└── playwright.config.ts         baseURL from PLAYWRIGHT_BASE_URL or http://localhost:8000
```

## API client (`src/lib/api.ts`)

- `fetchBoard`, `updateColumn`, `createCard`, `deleteCard`, `persistCardMove`
- `boardFromApi` maps numeric API ids to string ids for the Kanban model

## Running locally

```bash
cd frontend
npm install
npm run dev        # dev on :3000 — API calls go to same host only if proxied; use Docker or uvicorn for full stack
npm run build      # static export -> out/
npm run test:unit  # vitest (coverage thresholds in vitest.config.ts)
npm run test:e2e   # Playwright; requires running backend with **current** static export
```

## E2E against the real stack

Default `baseURL` is `http://localhost:8000` (Docker Compose). The served JS must match the repo: run `docker compose up --build` after frontend changes, or build and copy `frontend/out/` into `backend/static/` and run uvicorn.

Optional: `PLAYWRIGHT_BASE_URL=http://127.0.0.1:8001` for a local server on another port.

## Future

- **Part 10**: AI chat sidebar; refresh board when AI applies updates.
