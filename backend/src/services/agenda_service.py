"""Lógica de agenda: slots disponíveis, criação e cancelamento."""
import logging
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models import Agendamento, ConfigAgenda, Paciente

logger = logging.getLogger("agenda")
settings = get_settings()
TZ = ZoneInfo(settings.TZ)

DIA_KEY = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex", 5: "sab", 6: "dom"}


async def get_config(db: AsyncSession) -> ConfigAgenda:
    cfg = await db.get(ConfigAgenda, 1)
    if not cfg:
        cfg = ConfigAgenda(id=1)
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
    return cfg


async def _agendamentos_no_dia(db: AsyncSession, dia: date) -> list[Agendamento]:
    inicio = datetime.combine(dia, time(0, 0), tzinfo=TZ)
    fim = inicio + timedelta(days=1)
    q = (
        select(Agendamento)
        .where(
            and_(
                Agendamento.inicio >= inicio,
                Agendamento.inicio < fim,
                Agendamento.status.in_(("agendado", "confirmado")),
            )
        )
        .order_by(Agendamento.inicio)
    )
    res = await db.execute(q)
    return list(res.scalars())


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


async def listar_slots_dia(
    db: AsyncSession,
    dia: date,
    cfg: ConfigAgenda | None = None,
) -> list[datetime]:
    """Gera lista de slots de início disponíveis em um dia."""
    cfg = cfg or await get_config(db)

    chave = DIA_KEY[dia.weekday()]
    janela = (cfg.dias_trabalho or {}).get(chave)
    if not janela:
        return []

    inicio_h = _parse_hhmm(janela[0])
    fim_h = _parse_hhmm(janela[1])
    dur = timedelta(minutes=cfg.duracao_consulta_min)

    almoco = cfg.intervalo_almoco or {}
    almoco_ini = _parse_hhmm(almoco["inicio"]) if almoco.get("inicio") else None
    almoco_fim = _parse_hhmm(almoco["fim"]) if almoco.get("fim") else None

    ocupados = await _agendamentos_no_dia(db, dia)
    ocupados_ranges = [(a.inicio, a.fim) for a in ocupados]

    slots: list[datetime] = []
    cursor = datetime.combine(dia, inicio_h, tzinfo=TZ)
    limite = datetime.combine(dia, fim_h, tzinfo=TZ)
    agora = datetime.now(TZ)

    while cursor + dur <= limite:
        fim_slot = cursor + dur

        # Bloqueia se passou
        if cursor <= agora:
            cursor = fim_slot
            continue

        # Bloqueia se cai no almoço
        if almoco_ini and almoco_fim:
            ai = datetime.combine(dia, almoco_ini, tzinfo=TZ)
            af = datetime.combine(dia, almoco_fim, tzinfo=TZ)
            if cursor < af and fim_slot > ai:
                cursor = af
                continue

        # Bloqueia se conflita com agendamento existente
        conflito = any(not (fim_slot <= o_ini or cursor >= o_fim) for o_ini, o_fim in ocupados_ranges)
        if conflito:
            cursor = fim_slot
            continue

        slots.append(cursor)
        cursor = fim_slot

    return slots


async def proximos_slots(
    db: AsyncSession,
    dias_max: int | None = None,
    limite: int = 6,
) -> list[datetime]:
    """Pega os próximos N slots disponíveis (varrendo dias)."""
    cfg = await get_config(db)
    dias_max = dias_max or cfg.janela_dias_futuros

    resultado: list[datetime] = []
    hoje = datetime.now(TZ).date()
    for d in range(dias_max):
        dia = hoje + timedelta(days=d)
        slots = await listar_slots_dia(db, dia, cfg)
        resultado.extend(slots)
        if len(resultado) >= limite:
            break
    return resultado[:limite]


async def criar_agendamento(
    db: AsyncSession,
    paciente: Paciente,
    inicio: datetime,
    origem: str = "bot",
    observacoes: str | None = None,
) -> Agendamento:
    cfg = await get_config(db)
    fim = inicio + timedelta(minutes=cfg.duracao_consulta_min)

    # Confere conflito
    q = select(Agendamento).where(
        and_(
            Agendamento.inicio < fim,
            Agendamento.fim > inicio,
            Agendamento.status.in_(("agendado", "confirmado")),
        )
    )
    res = await db.execute(q)
    if res.scalar_one_or_none():
        raise ValueError("slot já ocupado")

    ag = Agendamento(
        paciente_id=paciente.id,
        inicio=inicio,
        fim=fim,
        status="agendado",
        origem=origem,
        observacoes=observacoes,
    )
    db.add(ag)
    await db.commit()
    await db.refresh(ag)
    return ag


async def cancelar_agendamento(db: AsyncSession, agendamento_id: int) -> Agendamento | None:
    ag = await db.get(Agendamento, agendamento_id)
    if not ag:
        return None
    ag.status = "cancelado"
    await db.commit()
    await db.refresh(ag)
    return ag


async def proximo_agendamento_do_paciente(
    db: AsyncSession, paciente_id: int
) -> Agendamento | None:
    q = (
        select(Agendamento)
        .where(
            Agendamento.paciente_id == paciente_id,
            Agendamento.inicio >= datetime.now(TZ),
            Agendamento.status.in_(("agendado", "confirmado")),
        )
        .order_by(Agendamento.inicio)
        .limit(1)
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()


def formatar_slot(dt: datetime) -> str:
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    dt_local = dt.astimezone(TZ)
    return f"{dias[dt_local.weekday()]} {dt_local.strftime('%d/%m')} às {dt_local.strftime('%H:%M')}"
