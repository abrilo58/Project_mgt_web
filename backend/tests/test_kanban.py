from fastapi.testclient import TestClient

from main import app


def make_client() -> TestClient:
    return TestClient(app)


def login(client: TestClient) -> None:
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200


def backlog_column_id(board: dict) -> int:
    col = next(c for c in board["columns"] if c["title"] == "Backlog")
    return col["id"]


def discovery_column_id(board: dict) -> int:
    col = next(c for c in board["columns"] if c["title"] == "Discovery")
    return col["id"]


def test_get_board_structure():
    client = make_client()
    login(client)
    res = client.get("/api/board")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data and "name" in data
    assert data["name"] == "Kanban Studio"
    assert len(data["columns"]) == 5
    titles = [c["title"] for c in data["columns"]]
    assert titles == ["Backlog", "Discovery", "In Progress", "Review", "Done"]
    for c in data["columns"]:
        assert "id" in c and "position" in c and "cards" in c
        assert c["cards"] == []


def test_put_column_rename():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    col_id = backlog_column_id(board)
    res = client.put(f"/api/columns/{col_id}", json={"title": "Icebox"})
    assert res.status_code == 200
    assert res.json() == {
        "id": col_id,
        "title": "Icebox",
        "position": 0,
    }
    board2 = client.get("/api/board").json()
    assert board2["columns"][0]["title"] == "Icebox"


def test_post_card_appears_in_board():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    res = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "New task", "details": "Do it"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "New task"
    assert body["details"] == "Do it"
    assert body["column_id"] == cid
    board2 = client.get("/api/board").json()
    backlog = next(c for c in board2["columns"] if c["id"] == cid)
    assert len(backlog["cards"]) == 1
    assert backlog["cards"][0]["title"] == "New task"


def test_put_card_updates_fields():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    created = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "T1", "details": "D1"},
    ).json()
    card_id = created["id"]
    res = client.put(
        f"/api/cards/{card_id}",
        json={"title": "T2", "details": "D2"},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "T2"
    assert res.json()["details"] == "D2"


def test_delete_card_removes_from_board():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "X", "details": ""},
    ).json()["id"]
    res = client.delete(f"/api/cards/{card_id}")
    assert res.status_code == 204
    board2 = client.get("/api/board").json()
    backlog = next(c for c in board2["columns"] if c["id"] == cid)
    assert backlog["cards"] == []


def test_put_move_card_to_other_column():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    bl = backlog_column_id(board)
    disc = discovery_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": bl, "title": "Move me", "details": ""},
    ).json()["id"]
    res = client.put(
        f"/api/cards/{card_id}/move",
        json={"column_id": disc, "position": 0},
    )
    assert res.status_code == 200
    assert res.json()["column_id"] == disc
    board2 = client.get("/api/board").json()
    bl_col = next(c for c in board2["columns"] if c["id"] == bl)
    disc_col = next(c for c in board2["columns"] if c["id"] == disc)
    assert bl_col["cards"] == []
    assert len(disc_col["cards"]) == 1
    assert disc_col["cards"][0]["id"] == card_id


def test_unauthenticated_board_routes_return_401():
    client = make_client()
    assert client.get("/api/board").status_code == 401
    assert client.put("/api/columns/1", json={"title": "B"}).status_code == 401
    assert client.post("/api/cards", json={"column_id": 1, "title": "t"}).status_code == 401
    assert client.put("/api/cards/1", json={"title": "u"}).status_code == 401
    assert client.delete("/api/cards/1").status_code == 401
    assert client.put("/api/cards/1/move", json={"column_id": 1, "position": 0}).status_code == 401


def test_get_board_404_when_board_removed():
    client = make_client()
    login(client)
    from database import connect

    conn = connect()
    conn.execute("DELETE FROM cards")
    conn.execute("DELETE FROM columns")
    conn.execute("DELETE FROM boards")
    conn.commit()
    conn.close()
    assert client.get("/api/board").status_code == 404


def test_rename_column_404_unknown_id():
    client = make_client()
    login(client)
    assert client.put("/api/columns/999999", json={"title": "Nope"}).status_code == 404


def test_create_card_404_unknown_column():
    client = make_client()
    login(client)
    res = client.post(
        "/api/cards",
        json={"column_id": 999999, "title": "x"},
    )
    assert res.status_code == 404


def test_create_card_400_position_out_of_range():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    res = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "x", "position": 5},
    )
    assert res.status_code == 400


def test_create_card_at_position_zero_shifts_existing():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    client.post("/api/cards", json={"column_id": cid, "title": "first", "details": ""})
    res = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "second", "position": 0},
    )
    assert res.status_code == 201
    col = next(c for c in client.get("/api/board").json()["columns"] if c["id"] == cid)
    assert [c["title"] for c in col["cards"]] == ["second", "first"]


def test_move_400_position_too_large_cross_column():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    bl = backlog_column_id(board)
    disc = discovery_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": bl, "title": "M", "details": ""},
    ).json()["id"]
    res = client.put(
        f"/api/cards/{card_id}/move",
        json={"column_id": disc, "position": 99},
    )
    assert res.status_code == 400


def test_move_400_position_too_large_same_column():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    bl = backlog_column_id(board)
    client.post("/api/cards", json={"column_id": bl, "title": "A", "details": ""})
    card_id = client.post(
        "/api/cards",
        json={"column_id": bl, "title": "B", "details": ""},
    ).json()["id"]
    res = client.put(
        f"/api/cards/{card_id}/move",
        json={"column_id": bl, "position": 99},
    )
    assert res.status_code == 400


def test_update_card_404_unknown_card():
    client = make_client()
    login(client)
    assert client.put("/api/cards/999999", json={"title": "z"}).status_code == 404


def test_update_card_400_empty_title():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "T", "details": ""},
    ).json()["id"]
    res = client.put(f"/api/cards/{card_id}", json={"title": "   "})
    assert res.status_code == 400


def test_update_card_same_column_id_no_position_no_move():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "Stay", "details": "d0"},
    ).json()["id"]
    res = client.put(f"/api/cards/{card_id}", json={"column_id": cid, "details": "d1"})
    assert res.status_code == 200
    assert res.json()["details"] == "d1"
    assert res.json()["column_id"] == cid


def test_update_card_move_column_only_appends():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    bl = backlog_column_id(board)
    disc = discovery_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": bl, "title": "Jump", "details": ""},
    ).json()["id"]
    res = client.put(f"/api/cards/{card_id}", json={"column_id": disc})
    assert res.status_code == 200
    assert res.json()["column_id"] == disc


def test_update_card_negative_position_400():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    cid = backlog_column_id(board)
    card_id = client.post(
        "/api/cards",
        json={"column_id": cid, "title": "P", "details": ""},
    ).json()["id"]
    res = client.put(f"/api/cards/{card_id}", json={"position": -1})
    assert res.status_code == 400


def test_delete_card_404():
    client = make_client()
    login(client)
    assert client.delete("/api/cards/999999").status_code == 404


def test_lifespan_init_runs_with_testclient_context():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200


def test_integration_multi_step_flow():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    c0 = board["columns"][0]["id"]
    c1 = board["columns"][1]["id"]

    client.put(f"/api/columns/{c0}", json={"title": "Todo"})
    card_id = client.post(
        "/api/cards",
        json={"column_id": c0, "title": "Card A", "details": "a"},
    ).json()["id"]
    client.put(
        f"/api/cards/{card_id}/move",
        json={"column_id": c1, "position": 0},
    )
    client.put(
        f"/api/columns/{c1}",
        json={"title": "Doing"},
    )
    client.delete(f"/api/cards/{card_id}")

    final = client.get("/api/board").json()
    col0 = next(c for c in final["columns"] if c["id"] == c0)
    col1 = next(c for c in final["columns"] if c["id"] == c1)
    assert col0["title"] == "Todo"
    assert col0["cards"] == []
    assert col1["title"] == "Doing"
    assert col1["cards"] == []
