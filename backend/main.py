import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import (
    system,
    webhook,
    pacientes,
    agendamentos,
    checkin,
    auth,
    config,
    whatsapp,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Sistema Médico",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)                       # /health, /api/info
app.include_router(webhook.router, prefix="/api")       # /api/webhook
app.include_router(auth.router, prefix="/api")          # /api/auth/*
app.include_router(pacientes.router, prefix="/api")     # /api/pacientes/*
app.include_router(agendamentos.router, prefix="/api")  # /api/agendamentos/*
app.include_router(checkin.router, prefix="/api")       # /api/checkin*
app.include_router(config.router, prefix="/api")        # /api/config
app.include_router(whatsapp.router, prefix="/api")      # /api/whatsapp/*


# ── Frontend estático (Next.js static export) ───────────────
# Servido na mesma origem que a API. Mount fica POR ÚLTIMO pra não
# capturar rotas da API.
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", "static/frontend"))
if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
