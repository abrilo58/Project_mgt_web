#!/bin/sh
# Ensure the data directory and db file are writable by appuser
# (the volume mount creates them as root on first run)
DATA_DIR="$(dirname "${DB_PATH:-/app/data/kanban.db}")"
mkdir -p "$DATA_DIR"
chown -R appuser:appuser "$DATA_DIR" 2>/dev/null || true

exec su -s /bin/sh appuser -c 'uv run uvicorn main:app --host 0.0.0.0 --port 8000'
