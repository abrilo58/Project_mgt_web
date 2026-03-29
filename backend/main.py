from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import (
    HARDCODED_PASSWORD,
    HARDCODED_USERNAME,
    create_session,
    delete_session,
    get_current_user,
)

app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(credentials: LoginRequest, response: Response):
    if credentials.username != HARDCODED_USERNAME or credentials.password != HARDCODED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
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
    response.delete_cookie("session_token")
    return {"ok": True}


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
