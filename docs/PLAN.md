# Project Plan: PM Kanban App MVP

## Test Coverage Standards

All parts with "comprehensive tests" require:
- **Minimum 80% unit test coverage** (lines/branches)
- **Robust integration tests** covering the happy path and key failure modes
- E2E tests where a user-facing flow is involved

---

## Part 1: Plan (complete)

- [x] Review existing frontend code
- [x] Create `frontend/AGENTS.md` describing the existing frontend
- [x] Enrich this PLAN.md with detailed substeps, checklists, and success criteria
- [x] User reviews and approves plan

**Success criteria:** User has signed off on the plan before any implementation begins.

---

## Part 2: Scaffolding

Set up Docker infrastructure, FastAPI backend, and start/stop scripts. Confirm a "hello world" response at `/` and a working API call.

### Substeps

- [x] Create `backend/` directory structure:
  - `main.py` — FastAPI app entry point
  - `pyproject.toml` — uv-managed dependencies (fastapi, uvicorn)
  - `.python-version` — pin Python version
- [x] FastAPI app serves:
  - `GET /api/health` — returns `{"status": "ok"}`
  - `GET /` — serves a placeholder `index.html` ("hello world") from a `static/` directory
- [x] Create `Dockerfile` in project root:
  - Multi-stage or single-stage image using `uv` as the Python package manager
  - Copies `backend/` into container
  - Runs `uvicorn` on port `8000`
  - Copies placeholder `static/index.html`
- [x] Create `docker-compose.yml` for local orchestration (single service, port 8000)
- [x] Create start/stop scripts in `scripts/`:
  - `start.sh` (Mac/Linux) — `docker compose up --build -d`
  - `start.bat` (Windows) — equivalent
  - `stop.sh` (Mac/Linux) — `docker compose down`
  - `stop.bat` (Windows) — equivalent
- [x] Update `scripts/AGENTS.md` describing the scripts
- [x] Update `backend/AGENTS.md` describing the backend structure

### Tests

- [x] `backend/tests/test_health.py` — unit test: `GET /api/health` returns 200 and `{"status": "ok"}` (uses FastAPI `TestClient`)
- [x] `backend/tests/test_static.py` — integration test: `GET /` returns 200 and HTML content
- [x] Manual smoke test: run start script, verify `http://localhost:8000/` shows "hello world" and `http://localhost:8000/api/health` returns JSON

### Success Criteria

- `docker compose up` builds and starts without errors
- `GET /` returns the placeholder HTML page
- `GET /api/health` returns `{"status": "ok"}`
- All backend tests pass with >= 80% coverage
- Start/stop scripts work on the target OS

---

## Part 3: Add Frontend

Statically build the Next.js frontend and serve it from FastAPI, so the Kanban board is accessible at `/`.

### Substeps

- [x] Configure `next.config.ts` for static export (`output: 'export'`)
- [x] Update `Dockerfile` to:
  - Stage 1: Node image — `npm ci && npm run build` inside `frontend/`
  - Stage 2: Python/uv image — copy `frontend/out/` into `backend/static/`
- [x] Remove the placeholder `static/index.html`; FastAPI now serves `frontend/out/` as static files using `StaticFiles` mount
- [x] Ensure Next.js image paths and asset prefixes work correctly when served from FastAPI root
- [x] Verify drag and drop and all existing Kanban functionality work in the Docker build (manual)

### Tests

- [x] Frontend unit tests still pass: `npm run test:unit` — 13/13 tests, 92.6% stmts / 90.12% branches
- [x] Frontend E2E tests passing: 3/3 (page load, add card, drag card) against Docker port 8000
- [x] Backend integration test: `GET /` returns 200 and contains expected HTML content
- [x] Manual smoke test: Docker build + `http://localhost:8000/` shows the full Kanban board

### Success Criteria

- Single `docker compose up` serves the full Kanban app at `http://localhost:8000/`
- All drag-and-drop and card interactions work in the served build
- All frontend unit tests pass with >= 80% coverage
- All backend tests pass with >= 80% coverage

---

## Part 4: Fake User Sign-In

Gate the Kanban board behind a login screen. Hardcoded credentials: `user` / `password`. Users can also log out.

### Substeps

- [x] Backend:
  - `POST /api/auth/login` — accepts `{ username, password }`, validates against hardcoded values, returns a session token (opaque UUID stored server-side in memory)
  - `POST /api/auth/logout` — invalidates the session token
  - `get_current_user` dependency to protect routes (will be used in Part 6+)
- [x] Frontend:
  - Create `src/app/login/page.tsx` — login form with username + password fields and submit button
  - Redirect unauthenticated users from `/` to `/login`
  - On successful login, httpOnly cookie set by backend; redirect to `/`
  - Add logout button to the board header; on click call `/api/auth/logout` and redirect to `/login`
  - Apply project color scheme to the login page

### Tests

- [x] Backend unit tests: 7 tests — valid/invalid login, me endpoint, logout invalidates session
- [x] E2E tests (Playwright): 7/7 passing — redirect, wrong credentials, correct login, sign out, board loads/adds/moves

### Success Criteria

- Visiting `/` without a session redirects to `/login`
- Login with `user` / `password` succeeds and shows the board
- Login with any other credentials shows an error and stays on `/login`
- Logout clears the session and redirects to `/login`
- All tests pass with >= 80% coverage

---

## Part 5: Database Modeling

Design the SQLite schema for the Kanban board and get sign-off before implementing it.

### Substeps

- [x] Propose a database schema covering:
  - `users` table (id, username — no password, hardcoded in app logic)
  - `boards` table (id, user_id, name)
  - `columns` table (id, board_id, title, position)
  - `cards` table (id, column_id, title, details, position)
- [x] Save schema as `docs/DATABASE.md`
- [x] User reviewed and approved the schema

### Success Criteria

- [x] `docs/DATABASE.md` documents the full schema
- [x] User approved schema before Part 6

---

## Part 6: Backend API

Implement API routes for reading and modifying the Kanban board. Create the SQLite database automatically if it does not exist.

### Substeps

- [x] Add SQLite integration using the approved schema (Part 5):
  - Use `sqlite3` stdlib or a lightweight ORM (e.g., SQLModel or raw sqlite3)
  - Database file path configurable via env var `DB_PATH` (default: `./data/kanban.db`)
  - Auto-create tables on startup if they do not exist
  - Seed the database with initial data for the authenticated user on first login
- [x] API routes (all require authentication):
  - `GET /api/board` — returns the current user's board (columns + cards in order)
  - `PUT /api/columns/{column_id}` — rename a column
  - `POST /api/cards` — create a new card in a column
  - `PUT /api/cards/{card_id}` — update a card (title, details, column, position)
  - `DELETE /api/cards/{card_id}` — delete a card
  - `PUT /api/cards/{card_id}/move` — move card to a different column and/or position
- [x] Update `backend/AGENTS.md` with route documentation

### Tests

- [x] Unit tests for each route using FastAPI `TestClient` with an in-memory SQLite DB:
  - `GET /api/board` returns correct structure
  - `PUT /api/columns/{id}` renames column; returns updated column
  - `POST /api/cards` creates card; appears in subsequent `GET /api/board`
  - `PUT /api/cards/{id}` updates card fields
  - `DELETE /api/cards/{id}` removes card from board
  - `PUT /api/cards/{id}/move` moves card; correct position in target column
  - Unauthenticated requests to all routes return 401
- [x] Integration tests: multi-step flows (create card, move it, rename column, delete card) against test DB

### Success Criteria

- All CRUD operations persist correctly to SQLite
- Fresh database is created automatically if `kanban.db` does not exist
- All routes return correct HTTP status codes and JSON shapes
- Unauthenticated access returns 401
- All tests pass with >= 80% coverage

---

## Part 7: Frontend + Backend Integration

Replace the in-memory demo state in the frontend with real backend API calls.

### Substeps

- [x] Create `src/lib/api.ts` — typed fetch wrapper for all API routes
- [x] Update `KanbanBoard.tsx`:
  - On mount: fetch board state from `GET /api/board`
  - On rename column: call `PUT /api/columns/{id}`
  - On add card: call `POST /api/cards`
  - On delete card: call `DELETE /api/cards/{id}`
  - On drag end (move card): call `PUT /api/cards/{id}/move`
  - Show loading state while initial fetch is in flight
  - Show error state if fetch fails
- [x] Remove `initialData` from `kanban.ts` (or keep for tests only)
- [x] Auth token is sent with every request (from cookie or header)
- [x] Handle 401 responses globally: redirect to `/login`

### Tests

- [x] Frontend unit tests: mock `api.ts` and verify each handler calls the correct endpoint
- [x] Frontend component tests: board renders correctly from mocked API response
- [x] E2E tests (Playwright):
  - Full flow: login → board loads → add card → card persists on reload
  - Rename column persists on reload
  - Delete card persists on reload
  - Drag card to new column persists on reload
- [x] Backend integration tests remain green

### Success Criteria

- Board data persists across page reloads
- All Kanban actions (add, rename, delete, move) persist to the database
- All E2E tests pass
- All tests pass with >= 80% coverage

---

## Part 8: AI Connectivity

Connect the backend to OpenRouter and verify a simple AI call works.

### Substeps

- [ ] Add `openai` Python package as a dependency (OpenRouter is OpenAI-compatible)
- [ ] Load `OPENROUTER_API_KEY` from environment (already in `.env`)
- [ ] Create `backend/ai.py` — thin wrapper for calling OpenRouter with model `openai/gpt-oss-120b`
- [ ] Add `POST /api/chat/test` route — sends a hardcoded "what is 2+2?" message to the AI and returns the raw response (dev/testing only)
- [ ] Verify the API key and model work end-to-end

### Tests

- [ ] Unit test `ai.py` with a mocked HTTP client: correct model, correct API base URL, key passed in header
- [ ] Integration test `POST /api/chat/test` with the real OpenRouter API (can be skipped in CI if no key available; mark with a skip marker)

### Success Criteria

- `POST /api/chat/test` returns a valid response from the AI
- The response to "what is 2+2?" is sensibly "4" (or equivalent)
- Unit tests pass without hitting the real API

---

## Part 9: AI Kanban Actions (Structured Outputs)

Extend the AI endpoint so it accepts the user's message plus conversation history, always includes the current Kanban board as context, and responds with structured output that may optionally update the board.

### Substeps

- [ ] Design Structured Output schema for AI response:
  ```json
  {
    "message": "string — the AI's reply to the user",
    "board_update": null | {
      "cards_to_create": [...],
      "cards_to_update": [...],
      "cards_to_delete": [...],
      "cards_to_move": [...]
    }
  }
  ```
- [ ] Update `ai.py` to:
  - Accept: `user_message`, `conversation_history`, `board_state`
  - Build system prompt that includes the board JSON and instructs the AI to use structured output
  - Request structured output using the OpenRouter/OpenAI response format
  - Return parsed `AIResponse` object
- [ ] Add `POST /api/chat` route:
  - Accepts `{ message: string, history: [...] }`
  - Fetches current board for the authenticated user
  - Calls AI with board context
  - If `board_update` is non-null, applies changes to the database
  - Returns `{ message, board_updated: bool }`
- [ ] Store conversation history server-side per user session (simple in-memory list is fine for MVP)

### Tests

- [ ] Unit tests for `ai.py` with mocked OpenRouter responses:
  - Parses `board_update: null` correctly (message only)
  - Parses `board_update` with create/update/delete/move correctly
  - Board JSON is included in the messages sent to AI
- [ ] Integration tests for `POST /api/chat`:
  - Message with no board action returns `board_updated: false`
  - Message that creates a card: card appears in `GET /api/board`
  - Message that moves a card: card is in new column in `GET /api/board`
  - Message that deletes a card: card absent from `GET /api/board`
  - Conversation history is included in subsequent calls

### Success Criteria

- AI responds to natural language questions about the board
- AI can create, move, and delete cards via conversation
- Board changes from AI are immediately reflected in `GET /api/board`
- All tests pass with >= 80% coverage

---

## Part 10: AI Chat Sidebar UI

Add a sidebar to the frontend with a full chat interface. If the AI updates the board, the UI refreshes automatically.

### Substeps

- [ ] Create `src/components/AIChatSidebar.tsx`:
  - Toggle button to open/close sidebar
  - Chat message list (user messages + AI responses, distinguished visually)
  - Text input and submit button
  - Loading indicator while awaiting AI response
  - Apply project color scheme (purple submit button, navy headings, etc.)
- [ ] Update `src/app/page.tsx`:
  - Render sidebar alongside `<KanbanBoard>`
  - Pass a `onBoardUpdate` callback to the sidebar
- [ ] In `KanbanBoard.tsx`: expose a `refresh()` method or accept a `refreshTrigger` prop that re-fetches the board from the API
- [ ] On AI response where `board_updated === true`: trigger board refresh automatically
- [ ] Maintain conversation history in sidebar state for display and pass prior messages to backend on each call

### Tests

- [ ] Component tests for `AIChatSidebar`:
  - Renders empty chat state
  - Submitting a message adds it to the conversation list
  - Loading state is shown while awaiting response
  - On `board_updated: true`, the `onBoardUpdate` callback is called
- [ ] E2E tests (Playwright):
  - Open sidebar, send a message, receive a response
  - Ask AI to create a card — card appears on the board without page reload
  - Ask AI to move a card — card moves to the correct column without page reload
  - Conversation history is preserved across multiple messages

### Success Criteria

- Chat sidebar is accessible from the main board page
- AI responses appear in the chat UI
- Board updates triggered by AI are reflected on the board without a manual reload
- Conversation is stateful within a session
- All tests pass with >= 80% coverage
