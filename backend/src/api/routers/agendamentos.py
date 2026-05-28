from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from src.api.deps import DB, admin_atual
from src.models import Agendamento, Paciente
from src.services import agenda_service, lembrete_service
from src.services.notify_service import notificar_secretaria

router = APIRouter(prefix="/agendamentos", tags=["agendamentos"], dependencies=[Depends(admin_atual)])


class AgendamentoIn(BaseModel):
    paciente_id: int
    inicio: datetime
    observacoes: str | None = None


class AgendamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    paciente_id: int
    inicio: datetime
    fim: datetime
    status: str
    origem: str
    observacoes: str | None


@router.get("/slots")
async def slots(db: DB, dia: date | None = None, limite: int = 20):
    if dia:
        return [s.isoformat() for s in await agenda_service.listar_slots_dia(db, dia)]
    return [s.isoformat() for s in await agenda_service.proximos_slots(db, limite=limite)]


@router.get("", response_model=list[AgendamentoOut])
async def listar(
    db: DB,
    de: datetime | None = Query(default=None),
    ate: datetime | None = Query(default=None),
    paciente_id: int | None = None,
):
    stmt = select(Agendamento).order_by(Agendamento.inicio)
    if de:
        stmt = stmt.where(Agendamento.inicio >= de)
    if ate:
        stmt = stmt.where(Agendamento.inicio <= ate)
    if paciente_id:
        stmt = stmt.where(Agendamento.paciente_id == paciente_id)
    res = await db.execute(stmt)
    return list(res.scalars())


@router.post("", response_model=AgendamentoOut)
async def criar(data: AgendamentoIn, db: DB):
    paciente = await db.get(Paciente, data.paciente_id)
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")
    try:
        ag = await agenda_service.criar_agendamento(
            db, paciente, data.inicio, origem="admin", observacoes=data.observacoes
        )
    except ValueError as e:
        raise HTTPException(409, str(e))
    await lembrete_service.agendar_lembretes_de(db, ag)
    await notificar_secretaria(
        f"📅 Agendado pelo painel: *{paciente.nome}* — "
        f"{agenda_service.formatar_slot(ag.inicio)}"
    )
    return ag


@router.post("/{ag_id}/cancelar", response_model=AgendamentoOut)
async def cancelar(ag_id: int, db: DB):
    ag = await agenda_service.cancelar_agendamento(db, ag_id)
    if not ag:
        raise HTTPException(404, "Não encontrado")
    paciente = await db.get(Paciente, ag.paciente_id)
    if paciente:
        await notificar_secretaria(
            f"❌ Cancelado pelo painel: *{paciente.nome}* — "
            f"{agenda_service.formatar_slot(ag.inicio)}"
        )
    return ag


@router.post("/{ag_id}/realizado", response_model=AgendamentoOut)
async def marcar_realizado(ag_id: int, db: DB):
    ag = await db.get(Agendamento, ag_id)
    if not ag:
        raise HTTPException(404, "Não encontrado")
    ag.status = "realizado"
    await db.commit()
    await db.refresh(ag)
    return ag
