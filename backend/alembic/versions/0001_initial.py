"""schema inicial — pacientes, agendamentos, lembretes, conversas, config, admin

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pacientes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=False, unique=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("cpf", sa.String(14), nullable=True),
        sa.Column("nascimento", sa.Date, nullable=True),
        sa.Column("assinatura_url", sa.String(500), nullable=True),
        sa.Column("assinou_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("origem", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ativo"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pacientes_telefone", "pacientes", ["telefone"], unique=True)

    op.create_table(
        "agendamentos",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("paciente_id", sa.BigInteger,
                  sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="agendado"),
        sa.Column("origem", sa.String(20), nullable=False, server_default="bot"),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agendamentos_inicio", "agendamentos", ["inicio"])
    op.create_index("ix_agendamentos_paciente_id", "agendamentos", ["paciente_id"])
    op.create_index("ix_agendamento_paciente_inicio", "agendamentos", ["paciente_id", "inicio"])

    op.create_table(
        "lembretes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("agendamento_id", sa.BigInteger,
                  sa.ForeignKey("agendamentos.id", ondelete="CASCADE"), nullable=True),
        sa.Column("paciente_id", sa.BigInteger,
                  sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("texto", sa.Text, nullable=False),
        sa.Column("disparar_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disparado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente"),
        sa.Column("erro_msg", sa.Text, nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lembretes_agendamento_id", "lembretes", ["agendamento_id"])
    op.create_index("ix_lembretes_paciente_id", "lembretes", ["paciente_id"])
    op.create_index("ix_lembretes_disparar_em", "lembretes", ["disparar_em"])
    op.create_index("ix_lembrete_status_disparar", "lembretes", ["status", "disparar_em"])

    op.create_table(
        "conversas",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("paciente_id", sa.BigInteger,
                  sa.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=False),
        sa.Column("direcao", sa.String(4), nullable=False),
        sa.Column("corpo", sa.Text, nullable=False),
        sa.Column("meta", postgresql.JSONB, nullable=True),
        sa.Column("estado_bot", sa.String(40), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_conversas_paciente_id", "conversas", ["paciente_id"])
    op.create_index("ix_conversas_telefone", "conversas", ["telefone"])
    op.create_index("ix_conversas_criado_em", "conversas", ["criado_em"])

    op.create_table(
        "config_agenda",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome_medico", sa.String(200), nullable=False, server_default="Dr."),
        sa.Column("dias_trabalho", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("duracao_consulta_min", sa.Integer, nullable=False, server_default="30"),
        sa.Column("intervalo_almoco", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("janela_dias_futuros", sa.Integer, nullable=False, server_default="14"),
        sa.Column("posvenda_dias", sa.Integer, nullable=False, server_default="180"),
        sa.Column("cadencia_lembrete", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # seed da linha única
    op.execute("""
        INSERT INTO config_agenda (id, nome_medico, dias_trabalho, intervalo_almoco, cadencia_lembrete)
        VALUES (
            1,
            'Dr.',
            '{"seg":["09:00","18:00"],"ter":["09:00","18:00"],"qua":["09:00","18:00"],"qui":["09:00","18:00"],"sex":["09:00","18:00"]}',
            '{"inicio":"12:00","fim":"13:00"}',
            '[
                {"tipo":"D-3","texto":"Oi {nome}! Lembrando da sua consulta com {medico} em {data} às {hora}. Posso confirmar?"},
                {"tipo":"D-1","texto":"Oi {nome}! Sua consulta é amanhã ({data}) às {hora}. Te espero!"},
                {"tipo":"D-0","texto":"Bom dia {nome}! Hoje às {hora} sua consulta. Até logo!"}
            ]'
        );
    """)

    op.create_table(
        "admin_users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("senha_hash", sa.String(200), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_table("admin_users")
    op.drop_table("config_agenda")
    op.drop_table("conversas")
    op.drop_table("lembretes")
    op.drop_table("agendamentos")
    op.drop_table("pacientes")
