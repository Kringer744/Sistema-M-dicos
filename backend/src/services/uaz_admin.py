"""Administração da instância UazAPI: criar, conectar (QR), status, desconectar, webhook."""
import logging
from typing import Any

import httpx

from src.core.config import get_settings

logger = logging.getLogger("uaz-admin")
settings = get_settings()


class UazAdminError(Exception):
    pass


def _headers_admin() -> dict:
    return {
        "admintoken": settings.UAZAPI_ADMIN_TOKEN,
        "Content-Type": "application/json",
    }


def _headers_instancia(token: str | None = None) -> dict:
    return {
        "token": token or settings.UAZAPI_TOKEN,
        "Content-Type": "application/json",
    }


async def _req(method: str, path: str, *, headers: dict, json: dict | None = None) -> Any:
    url = f"{settings.UAZAPI_BASE_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=30.0) as http:
        try:
            r = await http.request(method, url, headers=headers, json=json)
        except httpx.HTTPError as e:
            raise UazAdminError(f"falha de rede: {e}") from e
        if r.status_code >= 400:
            raise UazAdminError(f"{r.status_code}: {r.text[:300]}")
        try:
            return r.json()
        except Exception:
            return {"raw": r.text}


# ── Instância ────────────────────────────────────────────────

async def listar_instancias() -> list[dict]:
    """Lista todas as instâncias do servidor UazAPI."""
    data = await _req("GET", "/instance/all", headers=_headers_admin())
    if isinstance(data, list):
        return data
    return data.get("instances") or data.get("data") or []


async def buscar_instancia(nome: str) -> dict | None:
    instancias = await listar_instancias()
    for inst in instancias:
        if inst.get("name") == nome or inst.get("instance") == nome or inst.get("id") == nome:
            return inst
    return None


async def criar_instancia(nome: str) -> dict:
    """Cria a instância se não existir. Retorna o objeto da instância (com `token`)."""
    existente = await buscar_instancia(nome)
    if existente:
        return existente
    return await _req(
        "POST",
        "/instance/init",
        headers=_headers_admin(),
        json={"name": nome},
    )


async def status_instancia(token: str | None = None) -> dict:
    """Retorna status da instância: connected | connecting | disconnected, com QR se aplicável."""
    return await _req("GET", "/instance/status", headers=_headers_instancia(token))


async def conectar_instancia(token: str | None = None, phone: str | None = None) -> dict:
    """Inicia conexão. Retorna QR (base64) se desconectado."""
    body = {"phone": phone} if phone else {}
    return await _req(
        "POST",
        "/instance/connect",
        headers=_headers_instancia(token),
        json=body,
    )


async def desconectar_instancia(token: str | None = None) -> dict:
    return await _req("POST", "/instance/disconnect", headers=_headers_instancia(token))


async def reiniciar_instancia(token: str | None = None) -> dict:
    return await _req("POST", "/instance/restart", headers=_headers_instancia(token))


# ── Webhook ─────────────────────────────────────────────────

async def configurar_webhook(url: str, token: str | None = None) -> dict:
    """Configura webhook da instância pra apontar pro nosso endpoint."""
    body = {
        "url": url,
        "enabled": True,
        "events": [
            "messages",
            "messages.upsert",
            "connection",
        ],
        "excludeMessages": ["fromMe"],
        "addUrlEvents": False,
        "addUrlTypesMessages": False,
    }
    return await _req(
        "POST",
        "/webhook",
        headers=_headers_instancia(token),
        json=body,
    )


async def obter_webhook(token: str | None = None) -> dict:
    return await _req("GET", "/webhook", headers=_headers_instancia(token))


# ── Conveniências ──────────────────────────────────────────

async def garantir_instancia_e_token() -> tuple[dict, str]:
    """Garante que a instância existe e retorna (objeto_da_instancia, token)."""
    if not settings.UAZAPI_ADMIN_TOKEN:
        raise UazAdminError("UAZAPI_ADMIN_TOKEN não configurado")

    inst = await criar_instancia(settings.UAZAPI_INSTANCE)
    token = (
        inst.get("token")
        or inst.get("apiKey")
        or settings.UAZAPI_TOKEN
    )
    if not token:
        raise UazAdminError("não consegui obter o token da instância")
    return inst, token
