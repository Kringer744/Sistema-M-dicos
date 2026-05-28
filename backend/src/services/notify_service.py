"""Notificação pra secretária via WhatsApp."""
import logging

from src.core.config import get_settings
from src.services.uaz_client import get_uaz_client

logger = logging.getLogger("notify")
settings = get_settings()


async def notificar_secretaria(mensagem: str) -> None:
    if not settings.NOTIFICAR_SECRETARIA:
        return
    if not settings.SECRETARIA_TELEFONE:
        logger.warning("SECRETARIA_TELEFONE não configurado")
        return
    try:
        uaz = get_uaz_client()
        await uaz.enviar_texto(settings.SECRETARIA_TELEFONE, mensagem)
    except Exception as e:
        logger.exception("falha ao notificar secretária: %s", e)
