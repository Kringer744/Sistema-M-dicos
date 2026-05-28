#!/usr/bin/env bash
set -e

# ── Espera o Postgres responder (DNS + porta) ────────────────────
# Extrai host:porta da DATABASE_URL pra fazer probe TCP.
echo "→ Aguardando Postgres ficar disponível..."
python - <<'PY'
import os, re, socket, sys, time

url = os.environ.get("DATABASE_URL", "")
m = re.search(r"@([^:/?]+)(?::(\d+))?/", url)
if not m:
    print("DATABASE_URL não parece válida:", url)
    sys.exit(0)  # deixa o alembic dar o erro claro

host = m.group(1)
port = int(m.group(2) or 5432)

deadline = time.time() + 60
last_err = ""
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"✓ Postgres acessível em {host}:{port}")
            sys.exit(0)
    except Exception as e:
        last_err = str(e)
        time.sleep(2)

print(f"✗ Timeout esperando Postgres em {host}:{port} — último erro: {last_err}")
print("  Verifique se o serviço Postgres existe e se o hostname/porta no DATABASE_URL estão corretos.")
sys.exit(1)
PY

# ── Migrations ───────────────────────────────────────────────────
echo "→ Rodando migrations (alembic upgrade head)..."
alembic upgrade head

# ── Sobe o processo principal ────────────────────────────────────
case "${APP_MODE:-both}" in
  api)
    echo "→ Iniciando API (modo: api)"
    exec uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    echo "→ Iniciando Worker (modo: worker)"
    exec python -m src.services.worker_runner
    ;;
  both|*)
    echo "→ Iniciando API + Worker (modo: both)"
    python -m src.services.worker_runner &
    exec uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
esac
