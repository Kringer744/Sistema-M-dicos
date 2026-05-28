# Arquitetura — Sistema Médico

## Modelo de dados (resumo)

### `pacientes`
| coluna | tipo | obs |
|---|---|---|
| id | bigserial PK | |
| nome | text | |
| telefone | text UNIQUE | E.164 (`5511...`) |
| email | text NULL | |
| cpf | text NULL | |
| nascimento | date NULL | |
| assinatura_url | text NULL | path do termo assinado no tablet |
| assinou_em | timestamptz NULL | |
| origem | text | `tablet` / `whatsapp` / `manual` |
| status | text | `ativo` / `inativo` |
| criado_em | timestamptz | default now |
| atualizado_em | timestamptz | |

### `agendamentos`
| coluna | tipo | obs |
|---|---|---|
| id | bigserial PK | |
| paciente_id | FK | |
| inicio | timestamptz | |
| fim | timestamptz | |
| status | text | `agendado` / `confirmado` / `cancelado` / `realizado` / `faltou` |
| origem | text | `tablet` / `bot` / `admin` |
| observacoes | text NULL | |
| criado_em | timestamptz | |

Index: `(inicio)`, `(paciente_id, inicio DESC)`.

### `lembretes`
| coluna | tipo | obs |
|---|---|---|
| id | bigserial PK | |
| agendamento_id | FK | |
| tipo | text | `D-3` / `D-1` / `D-0` / `posvenda` |
| disparar_em | timestamptz | |
| disparado_em | timestamptz NULL | |
| status | text | `pendente` / `enviado` / `erro` / `cancelado` |
| erro_msg | text NULL | |

Index: `(status, disparar_em)` — pra worker varrer eficiente.

### `conversas`
| coluna | tipo | obs |
|---|---|---|
| id | bigserial PK | |
| paciente_id | FK NULL | |
| telefone | text | |
| direcao | text | `in` / `out` |
| corpo | text | |
| meta | jsonb | dados crus do webhook |
| estado_bot | text NULL | máquina de estados do fluxo |
| criado_em | timestamptz | |

### `config_agenda` (singleton — só o médico)
| coluna | tipo | obs |
|---|---|---|
| id | int PK | sempre 1 |
| dias_trabalho | jsonb | `{seg:[09:00,18:00],ter:...}` |
| duracao_consulta_min | int | default 30 |
| intervalo_almoco | jsonb | `[12:00,13:00]` |
| janela_dias_futuros | int | até quantos dias mostrar slots |
| posvenda_dias | int | quantos dias sem retorno dispara pós-venda |
| cadencia_lembrete | jsonb | `[{tipo:"D-3",texto:"..."}...]` |

## Fluxo de mensagens

```
[WhatsApp]
   │  (msg do paciente)
   ▼
[UazAPI webhook] ──> [FastAPI /webhook] ──> [Redis Stream: med:msg:in]
                                                    │
                                                    ▼
                                          [stream_worker.py]
                                                    │
                                                    ▼
                                          [bot_handler.py]
                                            consulta estado
                                            decide próxima ação
                                                    │
                                                    ▼
                                          [uaz_client.send()]
                                                    │
                                                    ▼
                                               [WhatsApp]
```

## Máquina de estados do bot

```
IDLE
  │ (recebe qualquer msg do paciente)
  ▼
AGUARDA_INTENCAO
  │ "agendar"               │ "cancelar"          │ "remarcar"
  ▼                         ▼                     ▼
LISTANDO_SLOTS         CONFIRMAR_CANCEL      LISTANDO_SLOTS_NOVO
  │ (paciente responde nº)                       │
  ▼                                              │
CONFIRMANDO_SLOT  ──────────────────────────────┘
  │ "sim"
  ▼
AGENDADO  → IDLE
```

## Workers

1. **stream_worker**: consome `med:msg:in` (Redis Stream), chama bot_handler. Latência alvo: <500ms.
2. **scheduler**: roda cron interno (APScheduler). A cada minuto verifica `lembretes` com `disparar_em <= now` e `status='pendente'`. Envia + marca enviado.
3. **posvenda**: cron diário 09:00. Pacientes sem agendamento futuro + último realizado há > `posvenda_dias`. Cria `lembrete` tipo `posvenda` pra disparar.

## Tablet (clínica)

Rota `/checkin` no Next.js — UI grande, touch-friendly:
1. Tela 1: pega nome + telefone + e-mail (ou busca por telefone se já existe)
2. Tela 2: termo de consentimento + assinatura (canvas)
3. Tela 3: "quer já agendar próximo retorno?" → grade de slots
4. Tela 4: confirmação + bot manda WhatsApp de boas-vindas

Backend: `POST /api/checkin` recebe payload completo, cria/atualiza paciente, salva assinatura (PNG base64), cria agendamento se selecionado, dispara WhatsApp de confirmação.
