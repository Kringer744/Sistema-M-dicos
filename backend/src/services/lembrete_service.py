"""Lembretes: agendamento, disparo e cadência."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import SessionLocal
from src.models import Agendamento, Conversa, Lembrete, Paciente
from src.services import agenda_service
from src.services.uaz_client import get_uaz_client

logger = logging.getLogger("lembrete")
settings = get_settings()
TZ = ZoneInfo(settings.TZ)


def _hora_disparo_padrao(dia: datetime) -> datetime:
    """Lembrete deve sair em horário humano: 9h da manhã do dia X."""
    return dia.replace(hour=9, minute=0, second=0, microsecond=0)


async def agendar_lembretes_de(db: AsyncSession, ag: Agendamento) -> list[Lembrete]:
    """Cria os lembretes D-3, D-1 e D-0 pra um agendamento."""
    cfg = await agenda_service.get_config(db)
    cadencia = cfg.cadencia_lembrete or []

    criados: list[Lembrete] = []
    inicio_local = ag.inicio.astimezone(TZ)
    agora = datetime.now(TZ)

    for item in cadencia:
        tipo = item.get("tipo")
        texto = item.get("texto", "")
        if tipo == "D-3":
            disparar = _hora_disparo_padrao(inicio_local - timedelta(days=3))
        elif tipo == "D-1":
            disparar = _hora_disparo_padrao(inicio_local - timedelta(days=1))
        elif tipo == "D-0":
            disparar = inicio_local.replace(hour=7, minute=0, second=0, microsecond=0)
        else:
            continue

        if disparar <= agora:
            continue  # já passou

        lembrete = Lembrete(
            agendamento_id=ag.id,
            paciente_id=ag.paciente_id,
            tipo=tipo,
            texto=texto,
            disparar_em=disparar,
        )
        db.add(lembrete)
        criados.append(lembrete)

    await db.commit()
    return criados


def _renderizar(template: str, paciente: Paciente, ag: Agendamento, nome_medico: str) -> str:
    inicio_local = ag.inicio.astimezone(TZ)
    return (
        template
        .replace("{nome}", paciente.nome.split()[0] if paciente.nome else "")
        .replace("{medico}", nome_medico)
        .replace("{data}", inicio_local.strftime("%d/%m"))
        .replace("{hora}", inicio_local.strftime("%H:%M"))
        .replace("{dia_semana}", agenda_service.formatar_slot(ag.inicio).split()[0])
    )


async def disparar_pendentes() -> int:
    """Roda periodicamente — varre lembretes pendentes e envia."""
    enviados = 0
    async with SessionLocal() as db:
        cfg = await agenda_service.get_config(db)
        agora = datetime.now(TZ)

        q = (
            select(Lembrete)
            .where(
                Lembrete.status == "pendente",
                Lembrete.disparar_em <= agora,
            )
            .limit(50)
        )
        res = await db.execute(q)
        lembretes = list(res.scalars())

        if not lembretes:
            return 0

        uaz = get_uaz_client()
        for lem in lembretes:
            try:
                paciente = await db.get(Paciente, lem.paciente_id)
                if not paciente:
                    lem.status = "erro"
                    lem.erro_msg = "paciente inexistente"
                    continue

                if lem.agendamento_id:
                    ag = await db.get(Agendamento, lem.agendamento_id)
                    if not ag or ag.status in ("cancelado", "realizado", "faltou"):
                        lem.status = "cancelado"
                        continue
                    texto = _renderizar(lem.texto, paciente, ag, cfg.nome_medico)
                else:
                    texto = lem.texto.replace(
                        "{nome}",
                        paciente.nome.split()[0] if paciente.nome else "",
                    ).replace("{medico}", cfg.nome_medico)

                await uaz.enviar_texto(paciente.telefone, texto)
                lem.status = "enviado"
                lem.disparado_em = agora
                enviados += 1

                db.add(Conversa(
                    paciente_id=paciente.id,
                    telefone=paciente.telefone,
                    direcao="out",
                    corpo=texto,
                    estado_bot=f"lembrete_{lem.tipo}",
                ))
            except Exception as e:
                logger.exception("falha disparo lembrete %s: %s", lem.id, e)
                lem.status = "erro"
                lem.erro_msg = str(e)[:300]

        await db.commit()
    return enviados
