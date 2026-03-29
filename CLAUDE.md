# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack Project Management MVP with a Kanban board and AI chat sidebar. Users sign in (hardcoded: `user` / `password`), manage cards via drag-and-drop, and interact with an AI assistant that can create/edit/move cards.

**Tech stack:** Next.js 16 (static export) + Python FastAPI + SQLite + OpenRouter AI + Docker

## Development Commands

### Backend (Python / uv)
```bash
cd backend
uv sync --extra dev          # Install dependencies
uv run uvicorn main:app --reload --port 8000  # Dev server

# Tests
uv run pytest                                  # Run all tests
uv run pytest tests/test_kanban.py            # Single test file
uv run pytest -k "test_create_card"           # Single test by name
uv run pytest --cov --cov-report=term-missing # With coverage (80% required)
```

### Frontend (Node / npm)
```bash
cd frontend
npm install
npm run dev                  # Next.js dev server (port 3000)
npm run build                # Static export to frontend/out/
npm run test                 # Vitest unit tests
npm run test:e2e             # Playwright E2E tests (requires running server on port 8000)
npm run test:all             # Both unit + E2E
```

### Docker (production / full-stack)
```bash
./scripts/start.sh           # Build and run (docker compose up --build -d)
./scripts/stop.sh            # docker compose down
docker compose logs -f       # View logs
```

The Docker build copies `frontend/out/` into `backend/static/`, where FastAPI serves it.

## Architecture

### Request Flow
1. Browser → FastAPI on port 8000
2. Auth: httpOnly `session_token` cookie; in-memory sessions dict
3. API routes: `/api/*` handled by FastAPI; all other routes serve `backend/static/` (Next.js static export)
4. AI: `POST /api/chat` → `backend/ai.py` → OpenRouter (OpenAI-compatible, `openai/gpt-oss-120b`)
5. After AI responds with `board_update`, client applies mutations in order: **delete → create → update → move**

### Backend (`backend/`)
| File | Role |
|------|------|
| `main.py` | App entry, auth routes, chat routes, static mount |
| `kanban_api.py` | APIRouter for board CRUD (`/api/board`, `/api/cards`, `/api/columns`) |
| `database.py` | SQLite init/schema, `get_db` dependency, seed data on first login |
| `ai.py` | OpenRouter client, `chat_kanban()` with structured board mutations |
| `ai_types.py` | Pydantic models: `ChatRequest`, `AIResponse`, `BoardUpdate` |
| `auth.py` | Cookie auth helpers, in-memory sessions |
| `chat_store.py` | In-memory chat transcript per session token |

### Frontend (`frontend/src/`)
| Path | Role |
|------|------|
| `app/page.tsx` | Auth gate; renders `<KanbanBoard>` + `<AIChatSidebar>` |
| `components/KanbanBoard.tsx` | Fetches board state, owns drag-and-drop logic (dnd-kit) |
| `components/AIChatSidebar.tsx` | Chat UI; triggers board refresh via `boardRefreshNonce` prop |
| `lib/api.ts` | Fetch helpers for all API calls |
| `lib/kanban.ts` | Types and `moveCard()` board state logic |
| `lib/dndIds.ts` | ID namespacing: `col-{id}` / `card-{id}` (avoids SQLite auto-increment collisions) |

### Database Schema
SQLite at `./data/kanban.db` (auto-created). One board per user → 5 fixed columns → cards with `position` ordering.

Tables: `users` → `boards` → `columns` → `cards`

Seeded automatically on first login (5 columns + sample cards unless `SKIP_DEMO_CARDS=1`).

## Key Conventions

- **Package manager:** `uv` for Python, `npm` for Node
- **Test coverage:** 80% minimum required (lines, branches, functions) for both backend and frontend
- **Frontend coverage exclusion:** `src/app/**` is excluded from unit test coverage (covered by E2E instead)
- **Integration tests:** marked `@pytest.mark.integration`; skipped automatically when `OPENROUTER_API_KEY` is unset
- **E2E tests:** require a running server at `http://localhost:8000` (or `PLAYWRIGHT_BASE_URL` env var); AI tests skipped without API key
- **Static export:** Next.js uses `output: "export"` — no server-side rendering, no API routes in frontend
- **Credentials:** `.env` file at project root contains `OPENROUTER_API_KEY`

## Color Palette
- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`
