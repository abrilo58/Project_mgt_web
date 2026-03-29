from unittest.mock import MagicMock, patch

import pytest

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


def test_chat_test_route_missing_key_returns_503():
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
        res = client.post("/api/chat/test")
    assert res.status_code == 503
