"""Estado de conversa armazenado em Redis (chave por telefone)."""
import json

from src.core.redis_client import get_redis

PREFIXO = "med:bot:state:"
TTL_SEGUNDOS = 60 * 60 * 6  # 6h


async def carregar(telefone: str) -> dict:
    r = get_redis()
    raw = await r.get(PREFIXO + telefone)
    return json.loads(raw) if raw else {}


async def salvar(telefone: str, estado: dict) -> None:
    r = get_redis()
    await r.set(PREFIXO + telefone, json.dumps(estado), ex=TTL_SEGUNDOS)


async def limpar(telefone: str) -> None:
    r = get_redis()
    await r.delete(PREFIXO + telefone)
