#!/usr/bin/env bash
set -e

echo "=== Starting ATLAS Backend Services ==="

# 1. Run database migrations at runtime (when all DB env vars are active)
echo "Running database migrations..."
alembic upgrade head || echo "Migration warning: proceeding with startup..."

# 2. Start Celery worker in the background (single process for 512MB RAM limit)
echo "Starting Celery background worker..."
celery -A app.workers.celery_app.celery_app worker --loglevel=info --concurrency=1 --pool=solo &

# 3. Start FastAPI Web Server in the foreground
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
