import os

from openai import OpenAI

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
