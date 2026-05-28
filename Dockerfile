# Dockerfile da raiz — atalho pra EasyPanel quando o App aponta pro repo todo
# (sem configurar Path /backend). Constrói o backend e roda api+worker juntos.
#
# Pra setup ideal use:
#   - App "api"     → Path /backend, APP_MODE=api
#   - App "worker"  → Path /backend, APP_MODE=worker
#   - App "frontend"→ Path /frontend
# Veja DEPLOY.md.

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

EXPOSE 8000

CMD ["bash", "start.sh"]
