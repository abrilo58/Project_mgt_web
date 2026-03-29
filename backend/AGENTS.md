# Backend - Agent Reference

## Overview

Python FastAPI backend. Serves the statically built Next.js frontend at `/` and exposes API routes under `/api/`. Runs in Docker via `uv`.

## Stack

- **Python 3.12**
- **FastAPI >= 0.115** — web framework
- **Uvicorn** — ASGI server
- **uv** — package manager (used inside Docker and locally)

## Directory Structure

```
backend/
├── main.py              Entry point; FastAPI app; mounts static files
├── pyproject.toml       Project metadata and dependencies (uv-managed)
├── .python-version      Pins Python to 3.12
├── static/              Static files served at /
│   └── index.html       Placeholder (replaced by Next.js build in Part 3+)
└── tests/
    ├── __init__.py
    ├── test_health.py   Tests for GET /api/health
    └── test_static.py   Tests for static file serving at GET /
```

## API Routes

| Method | Path | Description | Auth required |
|--------|------|-------------|---------------|
| GET | `/api/health` | Returns `{"status": "ok"}` | No |
| GET | `/` | Serves `static/index.html` | No |

## Running Locally (without Docker)

```bash
cd backend
uv sync --extra dev   # installs all deps including test deps
uv run uvicorn main:app --reload --port 8000
```

## Running Tests

```bash
cd backend
uv sync --extra dev
uv run pytest --cov --cov-report=term-missing
```

## Docker

The app is built and run via Docker Compose from the project root:

```bash
# From project root
docker compose up --build
```

The `Dockerfile` (project root):
1. Copies `backend/pyproject.toml` and runs `uv sync --no-dev`
2. Copies all of `backend/` into `/app`
3. Starts uvicorn on port 8000

## Notes for Future Parts

- **Part 3**: Replace `backend/static/index.html` with the Next.js static export (`frontend/out/`). Update the Dockerfile to build the frontend first.
- **Part 4**: Add `POST /api/auth/login` and `POST /api/auth/logout` routes; add auth middleware.
- **Part 6**: Add `GET /api/board` and CRUD routes for columns and cards; add SQLite database.
- **Part 8**: Add `ai.py` and `POST /api/chat` route for OpenRouter AI calls.
