from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Conversa(Base):
    __tablename__ = "conversas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    paciente_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    telefone: Mapped[str] = mapped_column(String(20), index=True)
    direcao: Mapped[str] = mapped_column(String(4))  # in | out
    corpo: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estado_bot: Mapped[str | None] = mapped_column(String(40), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
