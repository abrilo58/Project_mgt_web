import os
import secrets
import threading
import time

from fastapi import Cookie, HTTPException

HARDCODED_USERNAME = os.environ.get("APP_USERNAME", "user")
HARDCODED_PASSWORD = os.environ.get("APP_PASSWORD", "password")

SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", "86400"))  # 24h default
MAX_SESSIONS = 1000

# In-memory session store: token -> (username, created_at)
_lock = threading.Lock()
sessions: dict[str, tuple[str, float]] = {}


def _is_valid(entry: tuple[str, float]) -> bool:
    return (time.time() - entry[1]) < SESSION_TTL_SECONDS


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        # Evict expired sessions when approaching limit
        if len(sessions) >= MAX_SESSIONS:
            expired = [k for k, v in sessions.items() if not _is_valid(v)]
            for k in expired:
                del sessions[k]
        sessions[token] = (username, time.time())
    return token


def delete_session(token: str) -> None:
    with _lock:
        sessions.pop(token, None)


def get_current_user(session_token: str | None = Cookie(default=None)) -> str:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _lock:
        entry = sessions.get(session_token)
    if not entry or not _is_valid(entry):
        if entry:
            with _lock:
                sessions.pop(session_token, None)
        raise HTTPException(status_code=401, detail="Not authenticated")
    return entry[0]


def get_session_token(session_token: str | None = Cookie(default=None)) -> str:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _lock:
        entry = sessions.get(session_token)
    if not entry or not _is_valid(entry):
        if entry:
            with _lock:
                sessions.pop(session_token, None)
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token
