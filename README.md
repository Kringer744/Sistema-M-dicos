# Sistema Médico — Agenda + Lembretes WhatsApp

Sistema dedicado a um único cliente médico:
- Recepciona pacientes via tablet na clínica (assinatura digital)
- Conversa via WhatsApp (UazAPI) pra agendar/remarcar
- Dispara cadência de lembretes (D-3, D-1, dia)
- Reativa pacientes inativos (pós-venda)
- Painel admin (Next.js) pra ver agenda e conversas

## Stack
- **Backend**: FastAPI (Python 3.11) + SQLAlchemy + Alembic
- **DB**: PostgreSQL 15
- **Fila/Cache**: Redis 7 (streams pra webhook, scheduler pra lembretes)
- **WhatsApp**: UazAPI
- **Frontend**: Next.js 14 (App Router) + Tailwind
- **Deploy**: EasyPanel Hostinger (docker-compose)

## Estrutura

```
Sistema Médico/
├── backend/
│   ├── src/
│   │   ├── api/routers/        # endpoints HTTP
│   │   ├── core/               # config, db, redis
│   │   ├── models/             # SQLAlchemy
│   │   ├── services/           # regras de negócio
│   │   └── utils/
│   ├── alembic/                # migrations
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js admin
└── docker-compose.yml
```

## Fluxo principal

1. **Tablet (clínica)** → paciente assina → registro criado → pergunta retorno
2. **Bot WhatsApp** → manda slots numerados → paciente responde número → confirma
3. **Worker lembretes** → D-3, D-1, dia → mensagem automática
4. **Worker pós-venda** → diariamente vê quem não retorna há X dias → reativa

Ver [architecture.md](architecture.md) pra detalhes.
