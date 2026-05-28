from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from src.api.deps import DB, admin_atual
from src.models import Paciente

router = APIRouter(prefix="/pacientes", tags=["pacientes"], dependencies=[Depends(admin_atual)])


class PacienteIn(BaseModel):
    nome: str
    telefone: str
    email: str | None = None
    cpf: str | None = None
    nascimento: date | None = None
    origem: str = "manual"


class PacienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    telefone: str
    email: str | None
    status: str
    origem: str


@router.get("", response_model=list[PacienteOut])
async def listar(db: DB, q: str | None = None, limite: int = 100):
    stmt = select(Paciente).order_by(Paciente.criado_em.desc()).limit(limite)
    if q:
        stmt = stmt.where(Paciente.nome.ilike(f"%{q}%") | Paciente.telefone.ilike(f"%{q}%"))
    res = await db.execute(stmt)
    return list(res.scalars())


@router.post("", response_model=PacienteOut)
async def criar(data: PacienteIn, db: DB):
    telefone = "".join(c for c in data.telefone if c.isdigit())
    res = await db.execute(select(Paciente).where(Paciente.telefone == telefone))
    if res.scalar_one_or_none():
        raise HTTPException(409, "Paciente com esse telefone já existe")
    p = Paciente(**{**data.model_dump(), "telefone": telefone})
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.get("/{paciente_id}", response_model=PacienteOut)
async def obter(paciente_id: int, db: DB):
    p = await db.get(Paciente, paciente_id)
    if not p:
        raise HTTPException(404, "Não encontrado")
    return p
