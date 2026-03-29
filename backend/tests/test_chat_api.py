from unittest.mock import patch

from fastapi.testclient import TestClient

from ai_types import AIResponse, BoardUpdate, CardToCreate, CardToDelete, CardToMove, CardToUpdate
from main import app


def make_client() -> TestClient:
    return TestClient(app)


def login(client: TestClient) -> None:
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200


def backlog_column_id(board: dict) -> int:
    return next(c["id"] for c in board["columns"] if c["title"] == "Backlog")


def discovery_column_id(board: dict) -> int:
    return next(c["id"] for c in board["columns"] if c["title"] == "Discovery")


def test_chat_requires_auth():
    client = make_client()
    res = client.post("/api/chat", json={"message": "hello"})
    assert res.status_code == 401


def test_chat_no_board_update():
    client = make_client()
    login(client)
    with patch("main.ai_module.chat_kanban", return_value=AIResponse(message="Hello", board_update=None)):
        res = client.post("/api/chat", json={"message": "hi"})
    assert res.status_code == 200
    assert res.json() == {"message": "Hello", "board_updated": False}


def test_chat_creates_card():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    bid = backlog_column_id(board)
    bu = BoardUpdate(cards_to_create=[CardToCreate(column_id=bid, title="AI task", details="d")])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Added.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "add a card"})
    assert res.status_code == 200
    assert res.json()["board_updated"] is True
    board2 = client.get("/api/board").json()
    backlog = next(c for c in board2["columns"] if c["id"] == bid)
    assert any(c["title"] == "AI task" for c in backlog["cards"])


def test_chat_moves_card():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    backlog_id = backlog_column_id(board)
    disc_id = discovery_column_id(board)
    client.post("/api/cards", json={"column_id": backlog_id, "title": "Move me", "details": ""})
    board = client.get("/api/board").json()
    backlog_col = next(col for col in board["columns"] if col["id"] == backlog_id)
    card_id = backlog_col["cards"][0]["id"]
    bu = BoardUpdate(cards_to_move=[CardToMove(card_id=card_id, column_id=disc_id, position=0)])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Moved.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "move it"})
    assert res.status_code == 200
    assert res.json()["board_updated"] is True
    board2 = client.get("/api/board").json()
    disc = next(c for c in board2["columns"] if c["id"] == disc_id)
    assert any(c["id"] == card_id for c in disc["cards"])


def test_chat_updates_card_title():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    backlog_id = backlog_column_id(board)
    client.post("/api/cards", json={"column_id": backlog_id, "title": "Old", "details": "d"})
    board = client.get("/api/board").json()
    backlog_col = next(col for col in board["columns"] if col["id"] == backlog_id)
    card_id = backlog_col["cards"][0]["id"]
    bu = BoardUpdate(cards_to_update=[CardToUpdate(card_id=card_id, title="New title")])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Renamed.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "rename"})
    assert res.status_code == 200
    assert res.json()["board_updated"] is True
    board2 = client.get("/api/board").json()
    backlog = next(c for c in board2["columns"] if c["id"] == backlog_id)
    assert backlog["cards"][0]["title"] == "New title"


def test_chat_deletes_card():
    client = make_client()
    login(client)
    board = client.get("/api/board").json()
    backlog_id = backlog_column_id(board)
    client.post("/api/cards", json={"column_id": backlog_id, "title": "Delete me", "details": ""})
    board = client.get("/api/board").json()
    backlog_col = next(col for col in board["columns"] if col["id"] == backlog_id)
    card_id = backlog_col["cards"][0]["id"]
    bu = BoardUpdate(cards_to_delete=[CardToDelete(card_id=card_id)])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Gone.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "delete it"})
    assert res.status_code == 200
    assert res.json()["board_updated"] is True
    board2 = client.get("/api/board").json()
    backlog = next(c for c in board2["columns"] if c["id"] == backlog_id)
    assert all(c["id"] != card_id for c in backlog["cards"])


def test_chat_history_passed_on_second_call_when_omitted():
    client = make_client()
    login(client)
    captured: list[list[dict]] = []

    def fake_chat_kanban(user_message, conversation_history, board_state, **kwargs):
        captured.append(list(conversation_history))
        return AIResponse(message=f"echo:{user_message}", board_update=None)

    with patch("main.ai_module.chat_kanban", side_effect=fake_chat_kanban):
        client.post("/api/chat", json={"message": "first"})
        client.post("/api/chat", json={"message": "second"})
    assert captured[0] == []
    assert captured[1] == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "echo:first"},
    ]


def test_chat_respects_explicit_history_over_server_store():
    client = make_client()
    login(client)
    captured: list[list[dict]] = []

    def fake_chat_kanban(user_message, conversation_history, board_state, **kwargs):
        captured.append(list(conversation_history))
        return AIResponse(message="ok", board_update=None)

    custom = [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "old"}]
    with patch("main.ai_module.chat_kanban", side_effect=fake_chat_kanban):
        client.post("/api/chat", json={"message": "new", "history": custom})
    assert captured[0] == custom


def test_chat_503_when_api_key_missing():
    client = make_client()
    login(client)
    with patch(
        "main.ai_module.chat_kanban",
        side_effect=ValueError("OPENROUTER_API_KEY is not set"),
    ):
        res = client.post("/api/chat", json={"message": "x"})
    assert res.status_code == 503


def test_chat_502_on_invalid_ai_json():
    client = make_client()
    login(client)
    with patch(
        "main.ai_module.chat_kanban",
        side_effect=ValueError("Invalid AI response JSON: bad"),
    ):
        res = client.post("/api/chat", json={"message": "x"})
    assert res.status_code == 502


def test_chat_502_when_ai_uses_invalid_card_id():
    client = make_client()
    login(client)
    # AI hallucinates a card_id that does not exist — should return 502, not 404
    bu = BoardUpdate(cards_to_delete=[CardToDelete(card_id=99999)])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Done.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "delete card 99999"})
    assert res.status_code == 502
    assert "AI board update failed" in res.json()["detail"]


def test_chat_502_when_ai_uses_invalid_column_id():
    client = make_client()
    login(client)
    # AI hallucinates a column_id that does not exist — should return 502, not 404
    bu = BoardUpdate(cards_to_create=[CardToCreate(column_id=99999, title="Ghost", details="")])
    with patch(
        "main.ai_module.chat_kanban",
        return_value=AIResponse(message="Created.", board_update=bu),
    ):
        res = client.post("/api/chat", json={"message": "add a card to column 99999"})
    assert res.status_code == 502
    assert "AI board update failed" in res.json()["detail"]
