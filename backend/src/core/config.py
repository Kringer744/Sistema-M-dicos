from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    UAZAPI_BASE_URL: str
    UAZAPI_TOKEN: str = ""           # token da instância (envia mensagens)
    UAZAPI_ADMIN_TOKEN: str = ""     # adminToken (cria/conecta instâncias)
    UAZAPI_INSTANCE: str = "clinica" # nome da instância nesse servidor uazapi

    # LLM (OpenRouter)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-haiku-4-5"
    LLM_FALLBACK_MODEL: str = "openai/gpt-4o-mini"

    # Notificação secretária (E.164 sem +, ex 5511999999999)
    SECRETARIA_TELEFONE: str = ""
    NOTIFICAR_SECRETARIA: bool = True

    WEBHOOK_SECRET: str = "change-me"
    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_HOURS: int = 24

    APP_MODE: str = "both"  # api | worker | both
    TZ: str = "America/Sao_Paulo"

    POSVENDA_HORA_DIARIA: int = 9

    REDIS_STREAM_IN: str = "med:msg:in"
    REDIS_STREAM_GROUP: str = "med-workers"
    REDIS_STREAM_CONSUMER: str = "worker-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
