# Code Review

Reviewed against the codebase as of the `main` branch (post-Part 10). All findings were verified by reading source files directly. Issues are grouped by severity and category.

---

## Bugs

### B1 — AI board update errors expose wrong HTTP status (Medium)
**File:** `backend/kanban_api.py:375–410`

`apply_ai_board_update` calls `delete_card_data`, `create_card_data`, etc. directly. If the AI hallucinates an invalid `card_id` or `column_id`, `_card_for_user` or `_column_belongs_to_user` raises `HTTPException(404)`. This 404 propagates out of `POST /api/chat`, so the client receives a 404 "Card not found" response from a chat endpoint — misleading and hard to debug.

The database transaction in `get_db()` will correctly roll back the partial update, so there is no data corruption. The issue is purely in the error signal.

**Action:** Wrap the loop body in `apply_ai_board_update` with a try/except for `HTTPException` and re-raise as `HTTPException(502, detail=f"AI board update failed: {e.detail}")`.

---

### B2 — N+1 query in `get_board_data` (Low)
**File:** `backend/kanban_api.py:133–173`

For each column row, a separate `SELECT` is issued to fetch cards. For 5 columns this is 6 queries per board load. Called on every `GET /api/board` (including after every AI response that updates the board).

**Action:** Replace with a single join query and group results in Python, or use a single `SELECT ... WHERE column_id IN (...)`.

---

## Security

### S1 — Session cookie missing `secure` flag (Medium, production)
**File:** `backend/main.py:53`

```python
response.set_cookie("session_token", token, httponly=True, samesite="lax")
```

`secure=True` is absent. In production over HTTPS, this allows the cookie to be sent over plain HTTP if the browser ever makes an HTTP request to the same host, exposing the session token.

**Action:** Set `secure=True` when running in production. Can be conditional: `secure=os.environ.get("ENV") == "production"`.

---

### S2 — No maximum length on user-controlled text fields (Low)
**File:** `backend/kanban_api.py:185, 210`

`ColumnUpdate.title` and `CreateCardBody.title` use `Field(min_length=1)` but no `max_length`. An authenticated user can submit arbitrarily large strings, causing DB bloat and potentially inflating the board JSON sent to the AI on every chat message.

**Action:** Add `max_length=255` (or similar) to `title` and `details` fields in all Pydantic request models.

---

### S3 — Client-supplied history bypasses server-side store (Low, by design but worth noting)
**File:** `backend/main.py:90–92`

When `body.history` is not `None`, the client-provided array is used as the conversation history sent to the AI, bypassing the server-side `chat_store`. This means a client can craft arbitrary conversation history (e.g. injecting prior "assistant" instructions) for any request. There is no validation of the history contents.

This is a documented design trade-off (Part 9 notes client can pass history). For an MVP with a single hardcoded user it is acceptable, but should be revisited before adding real users.

**Action (future):** Remove the client history override path entirely and rely only on `chat_store`; or validate that client-supplied history entries contain only `role: user|assistant` and `content: str`.

---

## Code Quality

### Q1 — Message list uses index-based React keys (Low)
**File:** `frontend/src/components/AIChatSidebar.tsx:105`

```tsx
key={`${i}-${msg.role}`}
```

Index-based keys cause React to reuse DOM nodes incorrectly if messages are ever inserted in the middle or removed. Currently messages are only appended, so this doesn't trigger a bug today, but it is fragile.

**Action:** Add a `id` field (e.g. `crypto.randomUUID()`) to each message object when pushed to state, and use that as the key.

---

### Q2 — `check_same_thread=False` is required but undocumented (Low)
**File:** `backend/database.py:14`

```python
conn = sqlite3.connect(path, check_same_thread=False)
```

This is correct and necessary: FastAPI runs sync route handlers in a thread pool, so the connection created in the `get_db` generator (on one thread) is yielded to the route handler (potentially on a different thread). Without this flag, SQLite raises a `ProgrammingError`. However, the flag is unexplained, and a future reader might remove it thinking it is a safety compromise.

**Action:** Add a comment explaining why the flag is needed:
```python
# check_same_thread=False is required because FastAPI runs sync handlers in a
# thread pool; the connection is created by the get_db generator and passed
# to a route handler that may run on a different thread.
```

---

### Q3 — No keyboard submit in AI chat textarea (Low)
**File:** `frontend/src/components/AIChatSidebar.tsx:142–151`

The chat textarea has no `onKeyDown` handler. Users cannot press Enter (or Ctrl+Enter) to send a message — only the Send button works. This is a common expectation for chat interfaces.

**Action:** Add an `onKeyDown` handler: submit on `Ctrl+Enter` (or `Cmd+Enter` on Mac), allowing newlines otherwise.

---

### Q4 — `scrollToBottom` fires before assistant message renders (Low)
**File:** `frontend/src/components/AIChatSidebar.tsx:44, 56`

`scrollToBottom()` is called immediately after `setMessages(...)` but React state updates are async. The `requestAnimationFrame` inside `scrollToBottom` mitigates this in most cases, but on slow renders the scroll may land one message short.

**Action:** Move the post-response `scrollToBottom()` call into a `useEffect` that depends on `messages.length`, which fires after React commits the new message to the DOM.

---

## Testing Gaps

### T1 — No test for AI update with invalid IDs (Medium)
**File:** `backend/tests/test_chat_api.py`

There is no test verifying what happens when the AI returns a `board_update` containing a `card_id` that does not exist. As noted in B1, this currently returns a misleading 404.

**Action:** Add a test that mocks `chat_kanban` to return a `board_update` with a nonexistent `card_id` and asserts a 502 response (after B1 is fixed).

---

### T2 — No test for `POST /api/cards` with an explicit `position` (Low)
**File:** `backend/tests/test_kanban.py`

The `create_card_data` function has position-shifting logic (`UPDATE cards SET position = position + 1 WHERE position >= ?`) that only runs when `position` is explicitly provided. This code path has no test coverage.

**Action:** Add a test that creates a card at `position=0` in a column that already has cards, and verifies the existing cards shifted down.

---

### T3 — Playwright AI tests are skipped in CI (Low, documented)
**File:** `frontend/tests/kanban.spec.ts`

The 4 AI sidebar E2E tests are `test.skip` when `OPENROUTER_API_KEY` is unset, which is the normal CI state. This means the AI chat UI flow is only tested locally. This is documented in PLAN.md as intentional.

**Action (future):** Set up a CI secret for `OPENROUTER_API_KEY` and remove the skip guards, or add a mock-server mode for E2E AI tests.

---

## Deployment / Configuration

### D1 — No `.env.example` file (Low)
The project depends on `OPENROUTER_API_KEY`, `DB_PATH`, and `SKIP_DEMO_CARDS` but there is no `.env.example` documenting these. A new developer cloning the repo must discover them from reading source files.

**Action:** Create `.env.example`:
```
OPENROUTER_API_KEY=your_key_here
DB_PATH=./data/kanban.db
SKIP_DEMO_CARDS=0
```

---

## Intentional MVP Trade-offs (Not Action Items)

The following were flagged during review but are correct for this MVP and do not require changes:

| Item | Rationale |
|---|---|
| Hardcoded credentials (`user`/`password`) | Documented in `AGENTS.md` as deliberate MVP scope |
| In-memory session store | MVP; acceptable until real users or multi-instance deployment |
| In-memory chat history | Same as above |
| No CORS middleware | Not needed: Next.js static export is served by the same FastAPI server (same origin) |
| No API versioning | Out of scope for MVP |
| No rate limiting | Out of scope for MVP with single user |

---

## Summary

| Severity | Count |
|---|---|
| Medium | 3 (B1, S1, T1) |
| Low | 8 (B2, S2, S3, Q1–Q4, T2, T3, D1) |
| MVP trade-offs (no action) | 6 |

**Highest priority actions:** B1 (misleading error from AI chat), S1 (cookie security flag), S2 (missing max_length), T1 (test for B1 fix).
