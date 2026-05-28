"""Cliente OpenRouter pra LLM."""
import logging
import httpx

from src.core.config import get_settings

logger = logging.getLogger("llm")
settings = get_settings()


class LLMClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.fallback = settings.LLM_FALLBACK_MODEL
        self._http = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0,
        )

    async def chat(
        self,
        system: str,
        user: str,
        history: list[dict] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.4,
        response_format: dict | None = None,
    ) -> str:
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            body["response_format"] = response_format

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            r = await self._http.post("/chat/completions", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("llm primario falhou (%s), tentando fallback %s", e, self.fallback)
            body["model"] = self.fallback
            r = await self._http.post("/chat/completions", json=body, headers=headers)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def close(self):
        await self._http.aclose()


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
