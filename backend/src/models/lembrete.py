from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class Lembrete(Base):
    __tablename__ = "lembretes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agendamento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agendamentos.id", ondelete="CASCADE"), nullable=True, index=True
    )
    paciente_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=True, index=True
    )

    tipo: Mapped[str] = mapped_column(String(20))  # D-3 | D-1 | D-0 | posvenda
    texto: Mapped[str] = mapped_column(Text)

    disparar_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    disparado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pendente")
    # pendente | enviado | erro | cancelado
    erro_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    agendamento = relationship("Agendamento", back_populates="lembretes")

    __table_args__ = (
        Index("ix_lembrete_status_disparar", "status", "disparar_em"),
    )
