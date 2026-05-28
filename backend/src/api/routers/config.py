from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from src.api.deps import DB, admin_atual
from src.services import agenda_service

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(admin_atual)])


class ConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nome_medico: str
    dias_trabalho: dict
    duracao_consulta_min: int
    intervalo_almoco: dict
    janela_dias_futuros: int
    posvenda_dias: int
    cadencia_lembrete: list


class ConfigIn(BaseModel):
    nome_medico: str | None = None
    dias_trabalho: dict | None = None
    duracao_consulta_min: int | None = None
    intervalo_almoco: dict | None = None
    janela_dias_futuros: int | None = None
    posvenda_dias: int | None = None
    cadencia_lembrete: list | None = None


@router.get("", response_model=ConfigOut)
async def obter(db: DB):
    return await agenda_service.get_config(db)


@router.put("", response_model=ConfigOut)
async def atualizar(data: ConfigIn, db: DB):
    cfg = await agenda_service.get_config(db)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(cfg, k, v)
    await db.commit()
    await db.refresh(cfg)
    return cfg
