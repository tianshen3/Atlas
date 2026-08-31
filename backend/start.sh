#!/usr/bin/env bash
set -e

echo "=== Starting ATLAS Backend Services ==="

# 1. Start Celery worker in the background
echo "Starting Celery background worker..."
celery -A app.workers.celery_app.celery_app worker --loglevel=info &

# 2. Start FastAPI Web Server in the foreground
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
