from fastapi.testclient import TestClient

from main import app


def make_client() -> TestClient:
    return TestClient(app)


def login(client: TestClient) -> None:
    client.post("/api/auth/login", json={"username": "user", "password": "password"})


# --- Login ---

def test_login_valid_credentials():
    client = make_client()
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert "session_token" in client.cookies


def test_second_login_reuses_user_and_board():
    client = make_client()
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    client.post("/api/auth/logout")
    res = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert res.status_code == 200
    board = client.get("/api/board").json()
    assert board["name"] == "Kanban Studio"
    assert len(board["columns"]) == 5


def test_login_wrong_password():
    client = make_client()
    res = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert res.status_code == 401


def test_login_wrong_username():
    client = make_client()
    res = client.post("/api/auth/login", json={"username": "admin", "password": "password"})
    assert res.status_code == 401


# --- /api/auth/me ---

def test_me_authenticated():
    client = make_client()
    login(client)
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json() == {"username": "user"}


def test_me_unauthenticated():
    client = make_client()
    res = client.get("/api/auth/me")
    assert res.status_code == 401


# --- Logout ---

def test_logout_invalidates_session():
    client = make_client()
    login(client)
    client.post("/api/auth/logout")
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_logout_clears_cookie():
    client = make_client()
    login(client)
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert "session_token" not in client.cookies
