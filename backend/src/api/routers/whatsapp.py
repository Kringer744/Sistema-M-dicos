"""Endpoints pra gerenciar a conexão WhatsApp (UazAPI) pelo painel."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import admin_atual
from src.core.config import get_settings
from src.services import uaz_admin

logger = logging.getLogger("whatsapp-api")
settings = get_settings()

router = APIRouter(
    prefix="/whatsapp",
    tags=["whatsapp"],
    dependencies=[Depends(admin_atual)],
)


class StatusOut(BaseModel):
    instancia: str
    existe: bool
    status: str  # connected | connecting | disconnected | desconhecido
    telefone: str | None = None
    qrcode: str | None = None
    instance_token: str | None = None


class WebhookOut(BaseModel):
    url: str | None = None
    enabled: bool = False


def _normalizar_status(data: dict) -> tuple[str, str | None, str | None]:
    """Pega payload do /instance/status e devolve (status, telefone, qrcode)."""
    if not isinstance(data, dict):
        return "desconhecido", None, None

    # UazAPI varia o formato — cobrimos múltiplas chaves
    inst = data.get("instance") or data
    status = (
        inst.get("status")
        or inst.get("connectionStatus")
        or inst.get("state")
        or "desconhecido"
    )
    # normaliza pra inglês minúsculo
    status = str(status).lower()
    if status in ("open", "connected", "online"):
        status = "connected"
    elif status in ("connecting", "starting", "qrcode", "qr"):
        status = "connecting"
    elif status in ("close", "disconnected", "offline", "logged_out"):
        status = "disconnected"

    telefone = (
        inst.get("phone")
        or inst.get("wid")
        or inst.get("number")
        or data.get("phone")
    )
    qrcode = (
        inst.get("qrcode")
        or inst.get("qr")
        or inst.get("qrCode")
        or data.get("qrcode")
        or data.get("qr")
    )
    return status, telefone, qrcode


@router.get("/status", response_model=StatusOut)
async def status():
    try:
        inst, token = await uaz_admin.garantir_instancia_e_token()
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))

    try:
        data = await uaz_admin.status_instancia(token)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))

    st, telefone, qr = _normalizar_status(data)
    return StatusOut(
        instancia=settings.UAZAPI_INSTANCE,
        existe=bool(inst),
        status=st,
        telefone=telefone,
        qrcode=qr,
        instance_token=token,
    )


@router.post("/conectar", response_model=StatusOut)
async def conectar(phone: str | None = None):
    """Inicia o fluxo de conexão — retorna QR se desconectado."""
    try:
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        data = await uaz_admin.conectar_instancia(token, phone)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))

    # Após chamar connect, alguns servidores devolvem o QR aqui mesmo;
    # outros só via /status. Buscamos status final pra normalizar.
    try:
        st_data = await uaz_admin.status_instancia(token)
    except uaz_admin.UazAdminError:
        st_data = data

    st, tel, qr = _normalizar_status(st_data)
    # Se /status veio sem qr mas /connect trouxe, usa
    if not qr:
        _s, _t, qr2 = _normalizar_status(data)
        qr = qr2
    return StatusOut(
        instancia=settings.UAZAPI_INSTANCE,
        existe=True,
        status=st if st != "desconhecido" else "connecting",
        telefone=tel,
        qrcode=qr,
        instance_token=token,
    )


@router.post("/desconectar")
async def desconectar():
    try:
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        return await uaz_admin.desconectar_instancia(token)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))


@router.post("/reiniciar")
async def reiniciar():
    try:
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        return await uaz_admin.reiniciar_instancia(token)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))


class WebhookIn(BaseModel):
    url: str


@router.get("/webhook")
async def get_webhook():
    try:
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        return await uaz_admin.obter_webhook(token)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))


@router.post("/webhook")
async def set_webhook(data: WebhookIn):
    try:
        _inst, token = await uaz_admin.garantir_instancia_e_token()
        return await uaz_admin.configurar_webhook(data.url, token)
    except uaz_admin.UazAdminError as e:
        raise HTTPException(502, str(e))
