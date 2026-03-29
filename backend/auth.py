import secrets

from fastapi import Cookie, HTTPException

HARDCODED_USERNAME = "user"
HARDCODED_PASSWORD = "password"

# In-memory session store: token -> username
sessions: dict[str, str] = {}


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token


def delete_session(token: str) -> None:
    sessions.pop(token, None)


def get_current_user(session_token: str | None = Cookie(default=None)) -> str:
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_token]


def get_session_token(session_token: str | None = Cookie(default=None)) -> str:
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token
