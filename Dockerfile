# Build tudo-em-1: frontend (Next static export) + backend (FastAPI + worker).
# 1 App no EasyPanel + Postgres + Redis e tá pronto.

# ── Stage 1: build do frontend ────────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 2: backend Python + frontend estático ───────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo \
    APP_MODE=both

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copia o static export do Next pra ser servido pelo FastAPI
COPY --from=frontend /fe/out ./static/frontend

EXPOSE 8000

CMD ["bash", "start.sh"]
