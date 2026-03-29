# Backend - Agent Reference

## Overview

Python FastAPI backend. Serves the statically built Next.js frontend at `/` and exposes API routes under `/api/`. SQLite stores Kanban data per user. Runs in Docker via `uv`.

## Stack

- **Python 3.12**
- **FastAPI >= 0.115** — web framework
- **Uvicorn** — ASGI server
- **uv** — package manager (used inside Docker and locally)
- **sqlite3** (stdlib) — persistence; schema in `docs/DATABASE.md`

## Directory Structure

```
backend/
├── main.py           FastAPI app, lifespan (init DB), auth, `/api/chat`, `/api/chat/test`, static mount
├── ai.py             OpenRouter: `complete_chat`, `ask_what_is_two_plus_two`, `chat_kanban` (board + JSON reply)
├── ai_types.py       Pydantic: `ChatRequest`, `AIResponse`, `BoardUpdate`, card action payloads
├── chat_store.py     In-memory chat transcripts keyed by `session_token` (cleared on logout)
├── auth.py           Session cookie auth; `get_current_user`, `get_session_token`
├── database.py       DB path, schema init, `get_db` dependency, seed on login
├── kanban_api.py     REST board routes; `get_board_data`, `*_data` helpers, `apply_ai_board_update`
├── pyproject.toml
├── .python-version
├── static/           Next.js static export (build output)
└── tests/
    ├── conftest.py   Test DB path, schema init, per-test reset + session + chat clear
    ├── test_health.py
    ├── test_static.py
    ├── test_auth.py
    ├── test_ai.py
    ├── test_chat_api.py
    └── test_kanban.py
```

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `DB_PATH` | `./data/kanban.db` (resolved from cwd) | SQLite file path |
| `OPENROUTER_API_KEY` | (none) | Required for live OpenRouter calls (`/api/chat/test`, `/api/chat`); optional in CI (tests mock or skip) |

Tables are created on startup if missing. On each successful login, `ensure_user_board` creates the user row (if needed), then a board named "Kanban Studio" with five columns if the user has no board yet.

## API Routes

| Method | Path | Description | Auth required |
|--------|------|-------------|---------------|
| GET | `/api/health` | `{"status": "ok"}` | No |
| POST | `/api/auth/login` | Body `{username, password}`; sets httpOnly `session_token` cookie | No |
| POST | `/api/auth/logout` | Clears session | No |
| GET | `/api/auth/me` | `{"username": ...}` | Yes |
| GET | `/api/board` | Board id, name, columns (with nested cards, ordered) | Yes |
| PUT | `/api/columns/{column_id}` | Body `{"title"}`; rename column | Yes |
| POST | `/api/cards` | Body `column_id`, `title`, optional `details`, optional `position` | Yes |
| PUT | `/api/cards/{card_id}` | Optional `title`, `details`, `column_id`, `position` | Yes |
| DELETE | `/api/cards/{card_id}` | Remove card | Yes |
| PUT | `/api/cards/{card_id}/move` | Body `column_id`, `position` (0-based) | Yes |
| POST | `/api/chat/test` | Sends fixed prompt "what is 2+2?" to OpenRouter; returns `{"reply", "model"}` | Yes |
| POST | `/api/chat` | Body `message`, optional `history` (else server transcript); returns `message`, `board_updated`; applies structured `board_update` to SQLite | Yes |
| GET | `/` | Static site | No |

Unauthenticated access to protected routes returns **401**.

## Running Locally (without Docker)

```bash
cd backend
uv sync --extra dev
uv run uvicorn main:app --reload --port 8000
```

## Running Tests

```bash
cd backend
uv sync --extra dev
uv run pytest --cov --cov-report=term-missing
```

## Docker

From project root: `docker compose up --build`. Compose sets `DB_PATH=/app/data/kanban.db` and mounts `./data` to `/app/data` so the database survives container restarts.

## Notes for Future Parts

- **Part 7**: Frontend calls these routes instead of in-memory state (done).
- **Part 8**: `ai.py` and `POST /api/chat/test` (done).
- **Part 9**: `POST /api/chat`, `chat_kanban`, `apply_ai_board_update`, `ai_types`, `chat_store` (done).
- **Part 10**: Chat sidebar UI calling `/api/chat` with `credentials: "include"`.
