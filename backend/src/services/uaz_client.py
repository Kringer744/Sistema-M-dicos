"""Cliente UazAPI pra enviar mensagens WhatsApp.

Token é resolvido em runtime: se UAZAPI_TOKEN não estiver no env, busca pela
instância via adminToken (criando-a se não existir).
"""
import logging
import httpx

from src.core.config import get_settings

logger = logging.getLogger("uaz")
settings = get_settings()


class UazClient:
    def __init__(self):
        self.base_url = settings.UAZAPI_BASE_URL.rstrip("/")
        self._token: str | None = settings.UAZAPI_TOKEN or None
        self._http = httpx.AsyncClient(timeout=30.0)

    async def _resolver_token(self) -> str:
        if self._token:
            return self._token
        # late import pra evitar ciclo
        from src.services import uaz_admin
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        self._token = token
        return token

    async def _post(self, path: str, payload: dict) -> dict:
        token = await self._resolver_token()
        url = f"{self.base_url}{path}"
        headers = {"token": token, "Content-Type": "application/json"}
        try:
            r = await self._http.post(url, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            logger.error("uaz erro %s: %s", e.response.status_code, e.response.text)
            raise
        except Exception as e:
            logger.exception("uaz falha: %s", e)
            raise

    async def enviar_texto(self, telefone: str, texto: str) -> dict:
        return await self._post(
            "/send/text",
            {"number": telefone, "text": texto},
        )

    async def enviar_menu(self, telefone: str, texto: str, opcoes: list[str]) -> dict:
        linhas = [texto, ""]
        for i, opt in enumerate(opcoes, 1):
            linhas.append(f"*{i}*. {opt}")
        linhas.append("")
        linhas.append("_Responda apenas com o número._")
        return await self.enviar_texto(telefone, "\n".join(linhas))

    def invalidar_token(self) -> None:
        """Força nova resolução do token (chamar após reconectar/recriar instância)."""
        self._token = settings.UAZAPI_TOKEN or None

    async def close(self):
        await self._http.aclose()


_client: UazClient | None = None


def get_uaz_client() -> UazClient:
    global _client
    if _client is None:
        _client = UazClient()
    return _client
