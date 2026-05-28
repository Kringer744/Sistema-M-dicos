"""Endpoint do tablet da clínica: paciente assina e (opcional) já agenda retorno."""
import base64
import os
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from src.api.deps import DB
from src.models import Paciente
from src.services import agenda_service, lembrete_service
from src.services.notify_service import notificar_secretaria
from src.services.uaz_client import get_uaz_client

router = APIRouter(prefix="/checkin", tags=["checkin"])

STORAGE_DIR = Path(os.getenv("ASSINATURAS_DIR", "/data/assinaturas"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class CheckinIn(BaseModel):
    nome: str
    telefone: str
    email: str | None = None
    cpf: str | None = None
    nascimento: date | None = None
    assinatura_base64: str  # PNG em base64 (data:image/png;base64,XXXX OU só XXXX)
    agendar_retorno: bool = False
    slot_retorno: datetime | None = None


class CheckinOut(BaseModel):
    paciente_id: int
    agendamento_id: int | None
    proximos_slots: list[str]


@router.get("/slots")
async def slots_disponiveis(db: DB):
    """Pra UI do tablet montar grade."""
    slots = await agenda_service.proximos_slots(db, limite=12)
    return [s.isoformat() for s in slots]


@router.post("", response_model=CheckinOut)
async def checkin(data: CheckinIn, db: DB):
    telefone = "".join(c for c in data.telefone if c.isdigit())
    if not telefone:
        raise HTTPException(400, "Telefone inválido")

    # Salva assinatura
    b64 = data.assinatura_base64.split(",", 1)[-1]
    try:
        imagem = base64.b64decode(b64, validate=True)
    except Exception:
        raise HTTPException(400, "Assinatura inválida")

    nome_arq = f"{telefone}_{int(datetime.now().timestamp())}.png"
    caminho = STORAGE_DIR / nome_arq
    caminho.write_bytes(imagem)
    assinatura_url = str(caminho)

    # Upsert paciente
    res = await db.execute(select(Paciente).where(Paciente.telefone == telefone))
    paciente = res.scalar_one_or_none()
    if paciente:
        paciente.nome = data.nome
        paciente.email = data.email or paciente.email
        paciente.cpf = data.cpf or paciente.cpf
        paciente.nascimento = data.nascimento or paciente.nascimento
        paciente.assinatura_url = assinatura_url
        paciente.assinou_em = datetime.now()
        paciente.origem = paciente.origem or "tablet"
    else:
        paciente = Paciente(
            nome=data.nome,
            telefone=telefone,
            email=data.email,
            cpf=data.cpf,
            nascimento=data.nascimento,
            assinatura_url=assinatura_url,
            assinou_em=datetime.now(),
            origem="tablet",
            status="ativo",
        )
        db.add(paciente)
    await db.commit()
    await db.refresh(paciente)

    # Cria agendamento se solicitado
    agendamento_id = None
    if data.agendar_retorno and data.slot_retorno:
        try:
            ag = await agenda_service.criar_agendamento(
                db, paciente, data.slot_retorno, origem="tablet"
            )
            await lembrete_service.agendar_lembretes_de(db, ag)
            agendamento_id = ag.id

            # WhatsApp de boas-vindas + confirmação
            try:
                uaz = get_uaz_client()
                cfg = await agenda_service.get_config(db)
                msg = (
                    f"Olá {paciente.nome.split()[0]}! Aqui é da clínica do {cfg.nome_medico}. "
                    f"Recebi seu cadastro e agendei sua próxima consulta pra "
                    f"{agenda_service.formatar_slot(ag.inicio)}. "
                    f"Vou te lembrar antes!"
                )
                await uaz.enviar_texto(telefone, msg)
            except Exception:
                pass  # whatsapp não pode bloquear checkin

            await notificar_secretaria(
                f"🆕 Check-in tablet: *{paciente.nome}* — "
                f"agendado pra {agenda_service.formatar_slot(ag.inicio)}"
            )
        except ValueError:
            raise HTTPException(409, "Slot já ocupado")
    else:
        await notificar_secretaria(f"🆕 Check-in tablet: *{paciente.nome}* (sem agendar retorno)")

    proximos = await agenda_service.proximos_slots(db, limite=12)
    return CheckinOut(
        paciente_id=paciente.id,
        agendamento_id=agendamento_id,
        proximos_slots=[s.isoformat() for s in proximos],
    )
