#!/usr/bin/env bash
set -e

echo "=== Starting ATLAS Backend Services ==="

# 1. Run database migrations at runtime (when all DB env vars are active)
echo "Running database migrations..."
alembic upgrade head || echo "Migration warning: proceeding with startup..."

# 2. Start FastAPI Web Server in the foreground
# FastAPI's built-in BackgroundTasks handles PDF ingestion asynchronously
# without exceeding Render's 512MB RAM free tier limit.
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
