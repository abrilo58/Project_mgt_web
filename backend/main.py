import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai as ai_module
import chat_store
from ai_types import ChatRequest
from auth import (
    HARDCODED_PASSWORD,
    HARDCODED_USERNAME,
    create_session,
    delete_session,
    get_current_user,
    get_session_token,
)
from database import ensure_user_board, get_db, init_database
from kanban_api import apply_ai_board_update, get_board_data, router as kanban_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(
    credentials: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
):
    if credentials.username != HARDCODED_USERNAME or credentials.password != HARDCODED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    ensure_user_board(conn, credentials.username)
    token = create_session(credentials.username)
    response.set_cookie("session_token", token, httponly=True, samesite="lax")
    return {"ok": True}


@app.get("/api/auth/me")
def me(username: str = Depends(get_current_user)):
    return {"username": username}


@app.post("/api/auth/logout")
def logout(response: Response, session_token: str | None = Cookie(default=None)):
    if session_token:
        delete_session(session_token)
        chat_store.clear_history(session_token)
    response.delete_cookie("session_token")
    return {"ok": True}


@app.post("/api/chat/test")
def chat_test(username: str = Depends(get_current_user)):
    try:
        reply = ai_module.ask_what_is_two_plus_two()
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="AI is not configured (set OPENROUTER_API_KEY)",
        ) from None
    return {"reply": reply, "model": ai_module.DEFAULT_MODEL}


@app.post("/api/chat")
def chat_route(
    body: ChatRequest,
    username: str = Depends(get_current_user),
    session_token: str = Depends(get_session_token),
    conn: sqlite3.Connection = Depends(get_db),
):
    if body.history is not None:
        hist = [m.model_dump() for m in body.history]
    else:
        hist = chat_store.get_history(session_token)
    board = get_board_data(conn, username)
    try:
        parsed = ai_module.chat_kanban(body.message, hist, board)
    except ValueError as e:
        msg = str(e)
        if "OPENROUTER_API_KEY" in msg:
            raise HTTPException(
                status_code=503,
                detail="AI is not configured (set OPENROUTER_API_KEY)",
            ) from e
        raise HTTPException(status_code=502, detail=msg) from e
    board_updated = apply_ai_board_update(conn, username, parsed.board_update)
    chat_store.set_history(
        session_token,
        hist
        + [
            {"role": "user", "content": body.message},
            {"role": "assistant", "content": parsed.message},
        ],
    )
    return {"message": parsed.message, "board_updated": board_updated}


app.include_router(kanban_router, prefix="/api")

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
