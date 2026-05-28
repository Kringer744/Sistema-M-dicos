"""Pós-venda: identifica pacientes inativos e cria lembrete de reativação."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import SessionLocal
from src.models import Agendamento, Lembrete, Paciente
from src.services import agenda_service

logger = logging.getLogger("posvenda")
settings = get_settings()
TZ = ZoneInfo(settings.TZ)

TEXTO_PADRAO = (
    "Oi {nome}! Faz um tempinho que não passamos pelo consultório do {medico}. "
    "Que tal já agendar um retorno? Posso te mostrar os horários disponíveis!"
)


async def rodar_diariamente() -> int:
    """Encontra pacientes ativos sem agendamento futuro e cujo último realizado foi há > posvenda_dias."""
    criados = 0
    async with SessionLocal() as db:
        cfg = await agenda_service.get_config(db)
        agora = datetime.now(TZ)
        corte = agora - timedelta(days=cfg.posvenda_dias)

        # último agendamento realizado por paciente
        sub_realizado = (
            select(
                Agendamento.paciente_id,
                func.max(Agendamento.inicio).label("ultimo"),
            )
            .where(Agendamento.status == "realizado")
            .group_by(Agendamento.paciente_id)
            .subquery()
        )

        # paciente sem agendamento futuro
        sub_futuro = (
            select(Agendamento.paciente_id)
            .where(
                Agendamento.inicio >= agora,
                Agendamento.status.in_(("agendado", "confirmado")),
            )
            .distinct()
            .subquery()
        )

        q = (
            select(Paciente, sub_realizado.c.ultimo)
            .join(sub_realizado, sub_realizado.c.paciente_id == Paciente.id)
            .where(
                Paciente.status == "ativo",
                sub_realizado.c.ultimo <= corte,
                ~Paciente.id.in_(select(sub_futuro.c.paciente_id)),
            )
        )
        res = await db.execute(q)
        candidatos = res.all()

        # evita duplicar — só cria se não existe pós-venda pendente recente
        for paciente, ultimo in candidatos:
            existe_q = select(Lembrete).where(
                and_(
                    Lembrete.paciente_id == paciente.id,
                    Lembrete.tipo == "posvenda",
                    Lembrete.status.in_(("pendente", "enviado")),
                    Lembrete.criado_em >= agora - timedelta(days=30),
                )
            )
            existe = (await db.execute(existe_q)).scalar_one_or_none()
            if existe:
                continue

            db.add(Lembrete(
                paciente_id=paciente.id,
                tipo="posvenda",
                texto=TEXTO_PADRAO,
                disparar_em=agora.replace(hour=10, minute=0, second=0, microsecond=0),
            ))
            criados += 1

        if criados:
            await db.commit()
    return criados
