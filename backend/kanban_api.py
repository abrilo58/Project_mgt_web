import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_db

router = APIRouter(tags=["kanban"])


def _board_row(conn: sqlite3.Connection, username: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT b.id, b.name FROM boards b
        JOIN users u ON b.user_id = u.id
        WHERE u.username = ?
        """,
        (username,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Board not found")
    return row


def _column_for_board(conn: sqlite3.Connection, board_id: int, column_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, board_id, title, position FROM columns WHERE id = ? AND board_id = ?",
        (column_id, board_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Column not found")
    return row


def _card_for_user(conn: sqlite3.Connection, username: str, card_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT c.id, c.column_id, c.title, c.details, c.position
        FROM cards c
        JOIN columns col ON c.column_id = col.id
        JOIN boards b ON col.board_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE c.id = ? AND u.username = ?
        """,
        (card_id, username),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Card not found")
    return row


def _column_belongs_to_user(conn: sqlite3.Connection, username: str, column_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT col.id, col.board_id, col.title, col.position
        FROM columns col
        JOIN boards b ON col.board_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE col.id = ? AND u.username = ?
        """,
        (column_id, username),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Column not found")
    return row


def _apply_move(
    conn: sqlite3.Connection,
    username: str,
    card_id: int,
    dest_column_id: int,
    dest_position: int,
) -> None:
    card = _card_for_user(conn, username, card_id)
    _column_belongs_to_user(conn, username, dest_column_id)

    source_column_id = card["column_id"]
    source_pos = card["position"]

    if dest_position < 0:
        raise HTTPException(status_code=400, detail="Invalid position")

    if source_column_id == dest_column_id:
        ids = [
            r["id"]
            for r in conn.execute(
                "SELECT id FROM cards WHERE column_id = ? ORDER BY position, id",
                (source_column_id,),
            ).fetchall()
        ]
        if card_id not in ids:
            raise HTTPException(status_code=404, detail="Card not found")
        ids.remove(card_id)
        if dest_position > len(ids):
            raise HTTPException(status_code=400, detail="Invalid position")
        ids.insert(dest_position, card_id)
        for i, cid in enumerate(ids):
            conn.execute("UPDATE cards SET position = ? WHERE id = ?", (i, cid))
        return

    count_dest = conn.execute(
        "SELECT COUNT(*) AS n FROM cards WHERE column_id = ?",
        (dest_column_id,),
    ).fetchone()["n"]
    if dest_position > count_dest:
        raise HTTPException(status_code=400, detail="Invalid position")

    conn.execute(
        """
        UPDATE cards SET position = position - 1
        WHERE column_id = ? AND position > ?
        """,
        (source_column_id, source_pos),
    )
    conn.execute(
        """
        UPDATE cards SET position = position + 1
        WHERE column_id = ? AND position >= ?
        """,
        (dest_column_id, dest_position),
    )
    conn.execute(
        """
        UPDATE cards SET column_id = ?, position = ? WHERE id = ?
        """,
        (dest_column_id, dest_position, card_id),
    )


@router.get("/board")
def get_board(
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = _board_row(conn, username)
    columns_out = []
    col_rows = conn.execute(
        """
        SELECT id, title, position FROM columns
        WHERE board_id = ?
        ORDER BY position, id
        """,
        (board["id"],),
    ).fetchall()
    for col in col_rows:
        card_rows = conn.execute(
            """
            SELECT id, title, details, position FROM cards
            WHERE column_id = ?
            ORDER BY position, id
            """,
            (col["id"],),
        ).fetchall()
        columns_out.append(
            {
                "id": col["id"],
                "title": col["title"],
                "position": col["position"],
                "cards": [
                    {
                        "id": c["id"],
                        "title": c["title"],
                        "details": c["details"],
                        "position": c["position"],
                    }
                    for c in card_rows
                ],
            }
        )
    return {
        "id": board["id"],
        "name": board["name"],
        "columns": columns_out,
    }


class ColumnUpdate(BaseModel):
    title: str = Field(min_length=1)


@router.put("/columns/{column_id}")
def rename_column(
    column_id: int,
    body: ColumnUpdate,
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = _board_row(conn, username)
    col = _column_for_board(conn, board["id"], column_id)
    conn.execute(
        "UPDATE columns SET title = ? WHERE id = ?",
        (body.title.strip(), column_id),
    )
    return {
        "id": col["id"],
        "title": body.title.strip(),
        "position": col["position"],
    }


class CreateCardBody(BaseModel):
    column_id: int
    title: str = Field(min_length=1)
    details: str = ""
    position: int | None = None


@router.post("/cards", status_code=201)
def create_card(
    body: CreateCardBody,
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    _column_belongs_to_user(conn, username, body.column_id)
    count = conn.execute(
        "SELECT COUNT(*) AS n FROM cards WHERE column_id = ?",
        (body.column_id,),
    ).fetchone()["n"]

    if body.position is None:
        pos = count
    else:
        pos = body.position
        if pos < 0 or pos > count:
            raise HTTPException(status_code=400, detail="Invalid position")
        conn.execute(
            """
            UPDATE cards SET position = position + 1
            WHERE column_id = ? AND position >= ?
            """,
            (body.column_id, pos),
        )

    cur = conn.execute(
        """
        INSERT INTO cards (column_id, title, details, position)
        VALUES (?, ?, ?, ?)
        """,
        (body.column_id, body.title.strip(), body.details, pos),
    )
    new_id = cur.lastrowid
    row = conn.execute(
        "SELECT id, column_id, title, details, position FROM cards WHERE id = ?",
        (new_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "column_id": row["column_id"],
        "title": row["title"],
        "details": row["details"],
        "position": row["position"],
    }


class UpdateCardBody(BaseModel):
    title: str | None = None
    details: str | None = None
    column_id: int | None = None
    position: int | None = None


@router.put("/cards/{card_id}")
def update_card(
    card_id: int,
    body: UpdateCardBody,
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = _card_for_user(conn, username, card_id)
    new_title = body.title.strip() if body.title is not None else card["title"]
    new_details = card["details"] if body.details is None else body.details
    if body.title is not None and len(body.title.strip()) < 1:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    if body.column_id is not None or body.position is not None:
        dest_col = body.column_id if body.column_id is not None else card["column_id"]
        if body.position is not None:
            dest_pos = body.position
        elif dest_col != card["column_id"]:
            dest_pos = conn.execute(
                "SELECT COUNT(*) AS n FROM cards WHERE column_id = ?",
                (dest_col,),
            ).fetchone()["n"]
        else:
            dest_pos = card["position"]
        if dest_col != card["column_id"] or dest_pos != card["position"]:
            _apply_move(conn, username, card_id, dest_col, dest_pos)

    conn.execute(
        "UPDATE cards SET title = ?, details = ? WHERE id = ?",
        (new_title, new_details, card_id),
    )
    row = conn.execute(
        "SELECT id, column_id, title, details, position FROM cards WHERE id = ?",
        (card_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "column_id": row["column_id"],
        "title": row["title"],
        "details": row["details"],
        "position": row["position"],
    }


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(
    card_id: int,
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = _card_for_user(conn, username, card_id)
    col_id = card["column_id"]
    pos = card["position"]
    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.execute(
        """
        UPDATE cards SET position = position - 1
        WHERE column_id = ? AND position > ?
        """,
        (col_id, pos),
    )
    return None


class MoveCardBody(BaseModel):
    column_id: int
    position: int = Field(ge=0)


@router.put("/cards/{card_id}/move")
def move_card(
    card_id: int,
    body: MoveCardBody,
    username: str = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    _apply_move(conn, username, card_id, body.column_id, body.position)
    row = conn.execute(
        "SELECT id, column_id, title, details, position FROM cards WHERE id = ?",
        (card_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "column_id": row["column_id"],
        "title": row["title"],
        "details": row["details"],
        "position": row["position"],
    }
