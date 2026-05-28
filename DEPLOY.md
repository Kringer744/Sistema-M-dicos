# Deploy — EasyPanel Hostinger

## Pré-requisitos
- VPS com EasyPanel já instalado
- Instância UazAPI rodando com WhatsApp conectado
- Conta OpenRouter com créditos
- Domínio apontando pro IP da VPS (ex: `clinica.seudominio.com`)

## Passo a passo

### 1. Criar projeto no EasyPanel
- Novo projeto: `sistema-medico`

### 2. Subir repositório
```bash
cd "Sistema Médico"
git init
git add .
git commit -m "init"
git remote add origin git@github.com:seu-user/sistema-medico.git
git push -u origin main
```

### 3. Serviços no EasyPanel

**Postgres** (template oficial)
- Database: `sistema_medico`
- Username: `medico`
- Senha forte → guardar

**Redis** (template oficial)
- Sem senha (rede interna)

**API (App)**
- Build: Dockerfile em `backend/`
- Porta interna: `8000`
- Variáveis:
  ```
  APP_MODE=api
  DATABASE_URL=postgresql+asyncpg://medico:SENHA@$(project_name)_postgres:5432/sistema_medico
  REDIS_URL=redis://$(project_name)_redis:6379/0
  UAZAPI_BASE_URL=https://sua-instancia.uazapi.com
  UAZAPI_TOKEN=...
  UAZAPI_INSTANCE=clinica
  OPENROUTER_API_KEY=sk-or-v1-...
  SECRETARIA_TELEFONE=5511999999999
  WEBHOOK_SECRET=...
  JWT_SECRET=...
  TZ=America/Sao_Paulo
  ```
- Domínio: `api.clinica.seudominio.com`
- Health check: `/health`

**Worker (App)**
- Mesmo Dockerfile que API
- Sem domínio exposto
- Variáveis: idem API, **mas** `APP_MODE=worker`

**Frontend (App)**
- Build: Dockerfile em `frontend/`
- Porta interna: `3000`
- Variáveis:
  ```
  NEXT_PUBLIC_API_URL=https://api.clinica.seudominio.com
  ```
- Domínio: `clinica.seudominio.com`

### 4. Migrations
Rodam automaticamente no `start.sh` da API/worker (alembic upgrade head).

### 5. Configurar webhook UazAPI
Agora o painel faz isso pra você:
- Logar em `https://clinica.seudominio.com/whatsapp`
- Conectar (escanear QR)
- Clicar em **Salvar webhook** (a URL `https://api.clinica.seudominio.com/webhook` vem preenchida)

Alternativa manual no painel UazAPI:
- URL: `https://api.clinica.seudominio.com/webhook`
- Header customizado: `X-Webhook-Secret: <mesmo do .env>`
- Eventos: `messages.upsert` (ou equivalente)

### 6. Criar admin
```bash
curl -X POST https://api.clinica.seudominio.com/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"nome":"Dr Fulano","email":"medico@clinica.com","senha":"senha-forte"}'
```

### 7. Configurar agenda
- Logar no painel: `clinica.seudominio.com/login`
- Ir em **Config** → ajustar nome do médico, horários, duração, textos de lembrete

### 8. Tablet da clínica
- Abrir em modo kiosco: `clinica.seudominio.com/checkin`
- Rota não exige login (acesso público controlado pela rede da clínica)

## Smoke test pós-deploy

1. `curl https://api.../health` → `{"status":"ok"}`
2. Criar paciente manual via painel
3. Marcar agendamento pelo painel → ver secretária receber WhatsApp
4. Trocar `disparar_em` de um lembrete pra "agora" no DB → conferir disparo em 1 min
5. Fazer check-in via tablet → ver paciente criado + agendamento + WhatsApp de boas-vindas

## Monitoramento

- Logs: aba de logs do EasyPanel em cada serviço
- Métricas: pode adicionar Prometheus/Grafana depois (não inclusos no MVP)
