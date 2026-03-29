import os
import sqlite3
from pathlib import Path
from typing import Generator


def get_db_path() -> str:
    return os.environ.get("DB_PATH", str(Path("data/kanban.db").resolve()))


def connect() -> sqlite3.Connection:
    path = get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            position INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
        CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
        CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
        """
    )
    conn.commit()


def init_database() -> None:
    conn = connect()
    init_schema(conn)
    conn.close()


def reset_for_testing(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM cards")
    conn.execute("DELETE FROM columns")
    conn.execute("DELETE FROM boards")
    conn.execute("DELETE FROM users")
    conn.commit()


SEED_COLUMNS = [
    (0, "Backlog"),
    (1, "Discovery"),
    (2, "In Progress"),
    (3, "Review"),
    (4, "Done"),
]


def ensure_user_board(conn: sqlite3.Connection, username: str) -> None:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row:
        user_id = row["id"]
    else:
        cur = conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = cur.lastrowid

    board = conn.execute(
        "SELECT id FROM boards WHERE user_id = ?", (user_id,)
    ).fetchone()
    if board:
        return

    cur = conn.execute(
        "INSERT INTO boards (user_id, name) VALUES (?, ?)",
        (user_id, "Kanban Studio"),
    )
    board_id = cur.lastrowid
    for position, title in SEED_COLUMNS:
        conn.execute(
            "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, position),
        )


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

