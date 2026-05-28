#!/usr/bin/env bash
set -e

# Aplica migrations (idempotente)
alembic upgrade head

case "${APP_MODE:-both}" in
  api)
    exec uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec python -m src.services.worker_runner
    ;;
  both|*)
    python -m src.services.worker_runner &
    exec uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
esac
