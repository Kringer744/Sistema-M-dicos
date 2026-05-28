from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ConfigAgenda(Base):
    """Singleton — só existe a linha id=1, do médico."""
    __tablename__ = "config_agenda"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    nome_medico: Mapped[str] = mapped_column(String(200), default="Dr.")

    # {"seg":["09:00","18:00"], "ter":[...], ...}
    dias_trabalho: Mapped[dict] = mapped_column(JSONB, default=dict)
    duracao_consulta_min: Mapped[int] = mapped_column(Integer, default=30)
    intervalo_almoco: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"inicio":"12:00","fim":"13:00"}
    janela_dias_futuros: Mapped[int] = mapped_column(Integer, default=14)
    posvenda_dias: Mapped[int] = mapped_column(Integer, default=180)

    # [{"tipo":"D-3","texto":"Oi {nome}, lembrando da sua consulta dia {data} às {hora}..."}]
    cadencia_lembrete: Mapped[list] = mapped_column(JSONB, default=list)

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
