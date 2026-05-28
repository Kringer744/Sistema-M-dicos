"""Worker que consome o Redis Stream de mensagens recebidas."""
import asyncio
import json
import logging

from src.core.config import get_settings
from src.core.redis_client import get_redis
from src.services.bot_handler import processar_mensagem

logger = logging.getLogger("stream-worker")
settings = get_settings()


def _extrair_telefone_e_texto(payload: dict) -> tuple[str | None, str | None]:
    """Normaliza payload da UazAPI pra (telefone, texto)."""
    # Layout comum UazAPI: { data: { key: { remoteJid }, message: { conversation } } }
    data = payload.get("data") or payload.get("message") or payload

    telefone = None
    texto = None

    # telefone
    key = data.get("key") if isinstance(data, dict) else None
    if isinstance(key, dict):
        jid = key.get("remoteJid") or key.get("remote_jid")
        if jid:
            telefone = jid.split("@")[0]
    if not telefone:
        telefone = (
            data.get("from")
            or data.get("number")
            or data.get("sender")
            or payload.get("from")
        )

    # texto
    if isinstance(data, dict):
        msg = data.get("message") or {}
        if isinstance(msg, dict):
            texto = (
                msg.get("conversation")
                or (msg.get("extendedTextMessage") or {}).get("text")
                or (msg.get("imageMessage") or {}).get("caption")
            )
        if not texto:
            texto = data.get("text") or data.get("body") or data.get("content")

    if isinstance(telefone, str):
        telefone = "".join(ch for ch in telefone if ch.isdigit())

    return telefone, texto


async def _garantir_consumer_group():
    r = get_redis()
    try:
        await r.xgroup_create(
            settings.REDIS_STREAM_IN,
            settings.REDIS_STREAM_GROUP,
            id="0",
            mkstream=True,
        )
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise


async def run():
    await _garantir_consumer_group()
    r = get_redis()
    logger.info("stream worker iniciado: %s/%s",
                settings.REDIS_STREAM_IN, settings.REDIS_STREAM_GROUP)

    while True:
        try:
            resp = await r.xreadgroup(
                groupname=settings.REDIS_STREAM_GROUP,
                consumername=settings.REDIS_STREAM_CONSUMER,
                streams={settings.REDIS_STREAM_IN: ">"},
                count=10,
                block=5000,
            )
            if not resp:
                continue

            for _stream, mensagens in resp:
                for msg_id, campos in mensagens:
                    try:
                        payload = json.loads(campos.get("payload", "{}"))
                        telefone, texto = _extrair_telefone_e_texto(payload)
                        if telefone and texto:
                            await processar_mensagem(telefone, texto, raw=payload)
                        else:
                            logger.debug("payload sem texto/telefone: %s", payload)
                    except Exception as e:
                        logger.exception("erro processando msg %s: %s", msg_id, e)
                    finally:
                        await r.xack(settings.REDIS_STREAM_IN,
                                     settings.REDIS_STREAM_GROUP, msg_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("loop principal: %s", e)
            await asyncio.sleep(2)
