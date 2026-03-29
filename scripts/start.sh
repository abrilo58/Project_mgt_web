#!/usr/bin/env bash
set -e
docker compose up --build -d
echo "App running at http://localhost:8000"
