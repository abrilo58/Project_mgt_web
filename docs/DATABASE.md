# Database Schema

SQLite, created automatically on startup if it does not exist.

File path is configured via the `DB_PATH` environment variable (default: `./data/kanban.db`).

## Tables

### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL, UNIQUE |

No password column — credentials are hardcoded in application logic for the MVP.

### boards

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, FK → users(id) |
| name | TEXT | NOT NULL |

One board per user, created on first login.

### columns

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| board_id | INTEGER | NOT NULL, FK → boards(id) |
| title | TEXT | NOT NULL |
| position | INTEGER | NOT NULL |

`position` is a zero-based integer. Reordering a column updates the positions of all affected columns.

### cards

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| column_id | INTEGER | NOT NULL, FK → columns(id) |
| title | TEXT | NOT NULL |
| details | TEXT | NOT NULL DEFAULT '' |
| position | INTEGER | NOT NULL |

`position` is zero-based within its column. Moving a card updates the positions of affected cards in the source and/or target column.

## Relationships

```
users (1) ──< boards (1) ──< columns (many) ──< cards (many)
```

## Seed data

On first login, the backend creates:
- One board named "Kanban Studio"
- Five columns: Backlog (0), Discovery (1), In Progress (2), Review (3), Done (4)
- No cards — user starts with an empty board

## Indexes

- `users(username)` — unique index (implicit from UNIQUE constraint)
- `boards(user_id)` — for fast board lookup per user
- `cards(column_id)` — for fast card lookup per column
