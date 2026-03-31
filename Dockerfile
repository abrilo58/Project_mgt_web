# Stage 1: Build the Next.js frontend
FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (separate layer for cache efficiency)
COPY backend/pyproject.toml .
RUN uv sync --no-dev

# Copy backend application code
COPY backend/ .

# Replace placeholder static dir with the built frontend
COPY --from=frontend-build /frontend/out ./static

# Create non-root user and pre-create data dir
RUN useradd -r -m -s /bin/sh appuser && chown -R appuser /app \
    && mkdir -p /app/data && chown appuser:appuser /app/data \
    && chmod +x /app/entrypoint.sh

EXPOSE 8000

# Start as root so entrypoint can fix volume permissions, then drop to appuser
ENTRYPOINT ["/app/entrypoint.sh"]
