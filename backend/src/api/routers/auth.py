from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from src.api.deps import DB, criar_token, hash_senha, verificar_senha
from src.models import AdminUser

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class RegistroIn(BaseModel):
    email: EmailStr
    nome: str
    senha: str


@router.post("/login")
async def login(data: LoginIn, db: DB):
    q = select(AdminUser).where(AdminUser.email == data.email, AdminUser.ativo.is_(True))
    user = (await db.execute(q)).scalar_one_or_none()
    if not user or not verificar_senha(data.senha, user.senha_hash):
        raise HTTPException(401, "Credenciais inválidas")
    return {"token": criar_token(user.email), "nome": user.nome}


@router.post("/setup")
async def setup_inicial(data: RegistroIn, db: DB):
    """Cria o primeiro admin. Só funciona se a tabela admin_users estiver vazia."""
    res = await db.execute(select(AdminUser).limit(1))
    if res.scalar_one_or_none():
        raise HTTPException(403, "Setup já foi feito")
    user = AdminUser(
        email=data.email,
        nome=data.nome,
        senha_hash=hash_senha(data.senha),
    )
    db.add(user)
    await db.commit()
    return {"status": "ok", "token": criar_token(user.email)}
