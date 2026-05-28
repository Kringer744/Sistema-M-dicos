from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pacientes.id", ondelete="CASCADE"), index=True
    )

    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(20), default="agendado")
    # agendado | confirmado | cancelado | realizado | faltou

    origem: Mapped[str] = mapped_column(String(20), default="bot")  # tablet | bot | admin
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    paciente = relationship("Paciente", back_populates="agendamentos")
    lembretes = relationship("Lembrete", back_populates="agendamento", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agendamento_paciente_inicio", "paciente_id", "inicio"),
    )
