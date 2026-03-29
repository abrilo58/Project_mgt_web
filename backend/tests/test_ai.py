from unittest.mock import MagicMock, patch

import pytest

import json

import ai


def test_complete_chat_raises_without_key_or_client():
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            ai.complete_chat([{"role": "user", "content": "hi"}])


def test_complete_chat_handles_none_message_content():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = None
    mock_client.chat.completions.create.return_value = mock_resp

    out = ai.complete_chat([{"role": "user", "content": "x"}], client=mock_client)
    assert out == ""


def test_complete_chat_uses_openrouter_base_and_model():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "4"
    mock_client.chat.completions.create.return_value = mock_resp

    out = ai.complete_chat(
        [{"role": "user", "content": "what is 2+2?"}],
        client=mock_client,
        api_key="sk-not-used-when-client-set",
    )

    assert out == "4"
    mock_client.chat.completions.create.assert_called_once()
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == ai.DEFAULT_MODEL
    assert kwargs["messages"] == [{"role": "user", "content": "what is 2+2?"}]


def test_complete_chat_opens_client_with_key_and_base_url():
    mock_instance = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "ok"
    mock_instance.chat.completions.create.return_value = mock_resp

    with patch("ai.OpenAI", return_value=mock_instance) as MockOpenAI:
        ai.complete_chat(
            [{"role": "user", "content": "x"}],
            api_key="sk-test-key",
        )

    MockOpenAI.assert_called_once_with(
        base_url=ai.OPENROUTER_BASE_URL,
        api_key="sk-test-key",
    )


def test_ask_what_is_two_plus_two():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "The answer is 4."
    mock_client.chat.completions.create.return_value = mock_resp

    out = ai.ask_what_is_two_plus_two(client=mock_client)

    assert "4" in out
    msgs = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert msgs == [{"role": "user", "content": "what is 2+2?"}]


@pytest.mark.integration
def test_chat_test_route_real_openrouter():
    import os

    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    res = client.post("/api/chat/test")
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert data["model"] == ai.DEFAULT_MODEL
    assert "4" in data["reply"]


def test_chat_test_route_success_with_mock():
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    with patch.object(main.ai_module, "ask_what_is_two_plus_two", return_value="4"):
        res = client.post("/api/chat/test")
    assert res.status_code == 200
    assert res.json() == {"reply": "4", "model": ai.DEFAULT_MODEL}


def test_chat_test_route_requires_auth():
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    res = client.post("/api/chat/test")
    assert res.status_code == 401


def test_chat_kanban_includes_board_json_in_system_message():
    mock_cli = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = '{"message": "ok", "board_update": null}'
    mock_cli.chat.completions.create.return_value = mock_resp

    board = {"id": 7, "name": "Kanban Studio", "columns": [{"id": 3, "title": "Backlog", "position": 0, "cards": []}]}
    out = ai.chat_kanban("hello", [], board, client=mock_cli, api_key="sk-x")

    assert out.message == "ok"
    assert out.board_update is None
    kwargs = mock_cli.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}
    system = kwargs["messages"][0]["content"]
    assert "Current board:" in system
    assert json.dumps(7) in system or '"id": 7' in system


def test_chat_kanban_parses_full_board_update_shape():
    mock_cli = MagicMock()
    mock_resp = MagicMock()
    payload = {
        "message": "done",
        "board_update": {
            "cards_to_create": [{"column_id": 1, "title": "a", "details": "", "position": None}],
            "cards_to_update": [{"card_id": 2, "title": "b"}],
            "cards_to_delete": [{"card_id": 3}],
            "cards_to_move": [{"card_id": 4, "column_id": 5, "position": 0}],
        },
    }
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(payload)
    mock_cli.chat.completions.create.return_value = mock_resp

    out = ai.chat_kanban("x", [], {"id": 1, "name": "B", "columns": []}, client=mock_cli, api_key="sk-x")

    bu = out.board_update
    assert bu is not None
    assert bu.cards_to_create[0].title == "a"
    assert bu.cards_to_update[0].card_id == 2
    assert bu.cards_to_delete[0].card_id == 3
    assert bu.cards_to_move[0].column_id == 5


def test_chat_kanban_parses_board_update():
    mock_cli = MagicMock()
    mock_resp = MagicMock()
    payload = {
        "message": "Created.",
        "board_update": {"cards_to_create": [{"column_id": 1, "title": "T", "details": "", "position": None}]},
    }
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(payload)
    mock_cli.chat.completions.create.return_value = mock_resp

    out = ai.chat_kanban("add", [], {"id": 1, "name": "B", "columns": []}, client=mock_cli, api_key="sk-x")

    assert out.message == "Created."
    assert out.board_update is not None
    assert len(out.board_update.cards_to_create) == 1
    assert out.board_update.cards_to_create[0].title == "T"


def test_chat_kanban_raises_without_api_key_or_client():
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            ai.chat_kanban("x", [], {"id": 1, "name": "B", "columns": []})


def test_chat_kanban_raises_on_invalid_json_payload():
    mock_cli = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "not json"
    mock_cli.chat.completions.create.return_value = mock_resp

    with pytest.raises(ValueError, match="Invalid AI response JSON"):
        ai.chat_kanban("x", [], {"id": 1, "name": "B", "columns": []}, client=mock_cli, api_key="sk-x")


def test_chat_test_route_missing_key_returns_503():
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
        res = client.post("/api/chat/test")
    assert res.status_code == 503
