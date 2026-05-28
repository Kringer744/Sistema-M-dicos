from datetime import date, datetime
from sqlalchemy import BigInteger, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    telefone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)

    assinatura_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    assinou_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    origem: Mapped[str] = mapped_column(String(20), default="manual")  # tablet | whatsapp | manual
    status: Mapped[str] = mapped_column(String(20), default="ativo")    # ativo | inativo

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agendamentos = relationship("Agendamento", back_populates="paciente", lazy="selectin")
