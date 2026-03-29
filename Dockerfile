# Stage 1: Build the Next.js frontend
FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (separate layer for cache efficiency)
COPY backend/pyproject.toml .
RUN uv sync --no-dev

# Copy backend application code
COPY backend/ .

# Replace placeholder static dir with the built frontend
COPY --from=frontend-build /frontend/out ./static

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
