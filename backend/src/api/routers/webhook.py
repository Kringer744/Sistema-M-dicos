"""Recebe webhook da UazAPI e enfileira no Redis Stream."""
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from src.core.config import get_settings
from src.core.redis_client import get_redis

logger = logging.getLogger("webhook")
settings = get_settings()

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("")
async def receber_webhook(request: Request, x_webhook_secret: str | None = Header(default=None)):
    # Validação simples por header (UazAPI suporta custom headers)
    if settings.WEBHOOK_SECRET and x_webhook_secret != settings.WEBHOOK_SECRET:
        # Não bloqueia se não estiver setado — pra facilitar dev
        if x_webhook_secret is not None:
            raise HTTPException(403, "secret inválido")

    payload = await request.json()

    # Ignora eventos que não sejam mensagem recebida
    event = payload.get("event") or payload.get("type") or ""
    if event and "message" not in event.lower():
        return {"status": "ignored", "event": event}

    # Filtra mensagens enviadas pelo próprio bot (fromMe)
    data = payload.get("data") or payload.get("message") or payload
    if isinstance(data, dict) and (data.get("fromMe") or data.get("from_me")):
        return {"status": "ignored", "reason": "fromMe"}

    redis = get_redis()
    await redis.xadd(
        settings.REDIS_STREAM_IN,
        {"payload": json.dumps(payload)},
        maxlen=10000,
        approximate=True,
    )

    return {"status": "enqueued"}
