# session_token -> list of {"role": "user"|"assistant", "content": str}
CHAT_HISTORY: dict[str, list[dict[str, str]]] = {}


def clear_history(session_token: str) -> None:
    CHAT_HISTORY.pop(session_token, None)


def get_history(session_token: str) -> list[dict[str, str]]:
    return list(CHAT_HISTORY.get(session_token, []))


def set_history(session_token: str, messages: list[dict[str, str]]) -> None:
    CHAT_HISTORY[session_token] = messages


def clear_all() -> None:
    CHAT_HISTORY.clear()
