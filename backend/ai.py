import json
import os

from openai import OpenAI
from pydantic import ValidationError

from ai_types import AIResponse

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"


def complete_chat(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client: OpenAI | None = None,
) -> str:
    key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY")
    if not key and client is None:
        raise ValueError("OPENROUTER_API_KEY is not set")
    cli = client or OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)
    resp = cli.chat.completions.create(model=model, messages=messages)
    content = resp.choices[0].message.content
    if content is None:
        return ""
    return content


def ask_what_is_two_plus_two(
    *,
    client: OpenAI | None = None,
    api_key: str | None = None,
) -> str:
    return complete_chat(
        [{"role": "user", "content": "what is 2+2?"}],
        client=client,
        api_key=api_key,
    )


def chat_kanban(
    user_message: str,
    conversation_history: list[dict[str, str]],
    board_state: dict,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client: OpenAI | None = None,
) -> AIResponse:
    key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY")
    if not key and client is None:
        raise ValueError("OPENROUTER_API_KEY is not set")
    board_json = json.dumps(board_state, indent=2)
    system = (
        "You are a helpful assistant for the user's Kanban board. "
        "The board JSON lists columns (id, title, position) each with cards "
        "(id, title, details, position). Use only ids from this data for any board_update.\n\n"
        f"Current board:\n{board_json}\n\n"
        "Respond with a single JSON object only (no markdown). Shape:\n"
        '{"message": string, "board_update": null | object}\n'
        "If board_update is an object, it may contain:\n"
        '"cards_to_create": [{"column_id": int, "title": string, "details": string, "position": null|int}],\n'
        '"cards_to_update": [{"card_id": int, optional title, details, column_id, position}],\n'
        '"cards_to_delete": [{"card_id": int}],\n'
        '"cards_to_move": [{"card_id": int, "column_id": int, "position": int}].\n'
        "Use board_update null when no database changes. Use empty arrays for unused keys."
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    cli = client or OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)
    resp = cli.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        return AIResponse.model_validate_json(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid AI response JSON: {e}") from e
