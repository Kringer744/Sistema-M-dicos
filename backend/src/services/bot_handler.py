"""Bot conversacional do paciente — interpreta msg via LLM e executa ações."""
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import SessionLocal
from src.models import Conversa, Paciente
from src.services import agenda_service, bot_state
from src.services.llm_client import get_llm_client
from src.services.uaz_client import get_uaz_client
from src.services.notify_service import notificar_secretaria

logger = logging.getLogger("bot")
settings = get_settings()


SYSTEM_PROMPT = """Você é a assistente virtual da clínica do {medico}.
Seu papel: agendar consultas, confirmar lembretes, remarcar e cancelar.
Tom: cordial, direto, em português do Brasil. Mensagens curtas (máx 3 linhas).

REGRAS:
- Sempre que o paciente quiser agendar, ofereça até 6 opções de horário em lista numerada.
- Quando o paciente responder um número, é a escolha dele.
- Confirme antes de finalizar ("Confirmo {nome} para {dia} às {hora}? (sim/não)").
- Nunca invente horários — só ofereça os que estiverem na lista de SLOTS_DISPONIVEIS.
- Nunca prometa atendimento médico, não dê diagnóstico — só agenda/lembrete.

Responda APENAS em JSON válido no formato:
{
  "intencao": "agendar|confirmar|cancelar|remarcar|saudacao|outro",
  "escolha_slot": <índice 1-based da lista oferecida, se o paciente respondeu número, senão null>,
  "confirma": <true|false|null>,
  "resposta_para_paciente": "<o texto que o bot vai responder>",
  "concluiu_agendamento": <true|false>
}
"""


async def processar_mensagem(telefone: str, texto: str, raw: dict | None = None) -> None:
    """Ponto de entrada — chamado pelo stream worker pra cada mensagem recebida."""
    if not texto or not texto.strip():
        return

    async with SessionLocal() as db:
        paciente = await _buscar_paciente(db, telefone)

        # Log de entrada
        db.add(Conversa(
            paciente_id=paciente.id if paciente else None,
            telefone=telefone,
            direcao="in",
            corpo=texto,
            meta=raw or {},
        ))
        await db.commit()

        estado = await bot_state.carregar(telefone)

        # Se paciente não existe, ainda assim responde — pode ser lead novo
        # Idealmente o paciente já existe (veio do tablet ou de import inicial)
        if not paciente:
            await _responder_lead_desconhecido(db, telefone, texto)
            return

        await _ciclo_llm(db, paciente, telefone, texto, estado)


async def _buscar_paciente(db: AsyncSession, telefone: str) -> Paciente | None:
    q = select(Paciente).where(Paciente.telefone == telefone)
    res = await db.execute(q)
    return res.scalar_one_or_none()


async def _responder_lead_desconhecido(db: AsyncSession, telefone: str, texto: str) -> None:
    msg = (
        "Olá! Aqui é da clínica. Não encontrei seu cadastro. "
        "Por favor, passe na recepção pra fazermos seu cadastro inicial."
    )
    uaz = get_uaz_client()
    await uaz.enviar_texto(telefone, msg)
    db.add(Conversa(
        telefone=telefone,
        direcao="out",
        corpo=msg,
        estado_bot="lead_desconhecido",
    ))
    await db.commit()


async def _ciclo_llm(
    db: AsyncSession,
    paciente: Paciente,
    telefone: str,
    texto: str,
    estado: dict,
) -> None:
    cfg = await agenda_service.get_config(db)
    slots = await agenda_service.proximos_slots(db, limite=6)
    slots_formatados = [agenda_service.formatar_slot(s) for s in slots]
    slots_iso = [s.isoformat() for s in slots]

    contexto_extra = {
        "paciente_nome": paciente.nome,
        "slots_disponiveis": slots_formatados,
        "estado_anterior": estado,
        "data_hoje": datetime.now(agenda_service.TZ).strftime("%Y-%m-%d %H:%M"),
    }

    system = SYSTEM_PROMPT.format(medico=cfg.nome_medico)
    user_msg = (
        f"PACIENTE: {paciente.nome}\n"
        f"MENSAGEM: {texto}\n\n"
        f"CONTEXTO (JSON):\n{json.dumps(contexto_extra, ensure_ascii=False)}"
    )

    llm = get_llm_client()
    try:
        bruto = await llm.chat(
            system=system,
            user=user_msg,
            max_tokens=400,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        decisao = json.loads(bruto)
    except Exception as e:
        logger.exception("llm falhou: %s", e)
        decisao = {
            "intencao": "outro",
            "resposta_para_paciente": "Tive um problema agora. Pode repetir, por favor?",
            "concluiu_agendamento": False,
        }

    resposta = decisao.get("resposta_para_paciente") or "Em que posso te ajudar?"
    intencao = decisao.get("intencao") or "outro"
    escolha = decisao.get("escolha_slot")
    confirma = decisao.get("confirma")

    # Persistência do estado
    estado_novo: dict = {
        "intencao": intencao,
        "slots_oferecidos": slots_iso,
        "aguardando_confirmacao": False,
    }

    # Se LLM disse que paciente escolheu um slot, guardamos pra próxima msg confirmar
    if isinstance(escolha, int) and 1 <= escolha <= len(slots_iso):
        slot_iso = slots_iso[escolha - 1]
        estado_novo["slot_pendente"] = slot_iso
        estado_novo["aguardando_confirmacao"] = True

    # Se LLM disse que confirma e tem slot pendente do estado anterior, marca
    slot_pendente_iso = estado.get("slot_pendente") if confirma else None
    if confirma is True and slot_pendente_iso:
        slot_dt = datetime.fromisoformat(slot_pendente_iso)
        try:
            ag = await agenda_service.criar_agendamento(
                db, paciente, slot_dt, origem="bot"
            )
            from src.services.lembrete_service import agendar_lembretes_de
            await agendar_lembretes_de(db, ag)
            resposta = (
                f"Agendado! {agenda_service.formatar_slot(slot_dt)} "
                f"com {cfg.nome_medico}. Vou te lembrar antes!"
            )
            await notificar_secretaria(
                f"📅 Novo agendamento: *{paciente.nome}* — "
                f"{agenda_service.formatar_slot(slot_dt)} (via bot)"
            )
            estado_novo = {}  # reset
        except ValueError:
            resposta = "Esse horário acabou de ser pego por outra pessoa. Quer escolher outro?"
            estado_novo.pop("slot_pendente", None)
            estado_novo["aguardando_confirmacao"] = False
    elif confirma is False and slot_pendente_iso:
        resposta = "Tudo bem, qual outro horário fica melhor?"
        estado_novo.pop("slot_pendente", None)
        estado_novo["aguardando_confirmacao"] = False

    if intencao == "cancelar":
        prox = await agenda_service.proximo_agendamento_do_paciente(db, paciente.id)
        if prox:
            await agenda_service.cancelar_agendamento(db, prox.id)
            resposta = (
                f"Cancelei seu agendamento de "
                f"{agenda_service.formatar_slot(prox.inicio)}. Quer reagendar?"
            )
            await notificar_secretaria(
                f"❌ Cancelamento: *{paciente.nome}* — "
                f"{agenda_service.formatar_slot(prox.inicio)}"
            )

    await bot_state.salvar(telefone, estado_novo)

    uaz = get_uaz_client()
    await uaz.enviar_texto(telefone, resposta)

    db.add(Conversa(
        paciente_id=paciente.id,
        telefone=telefone,
        direcao="out",
        corpo=resposta,
        estado_bot=intencao,
        meta={"llm_decisao": decisao},
    ))
    await db.commit()
