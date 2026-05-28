# Deploy — EasyPanel Hostinger (modelo simplificado)

**Tudo em 1 App** — o FastAPI serve a API em `/api/*` e o frontend Next.js (static export) em `/`.
Você só precisa de 3 serviços no EasyPanel:

1. Postgres
2. Redis
3. App (esse repo)

## Passo a passo

### 1. Subir código
```bash
git clone https://github.com/Kringer744/Sistema-M-dicos.git
# (ou usar o repo direto no EasyPanel via OAuth do GitHub)
```

### 2. Criar projeto no EasyPanel
- Novo projeto: `sistema-medico` (ou o nome que preferir)

### 3. Postgres (template oficial)
- Database: `sistema_medico`
- Username: `medico`
- Senha forte → guardar

### 4. Redis (template oficial)
- Sem senha (rede interna)

### 5. App principal (Source = GitHub)
- **Repository**: `Kringer744/Sistema-M-dicos`
- **Branch**: `main`
- **Path**: deixar vazio (Dockerfile está na raiz)
- **Port**: `8000`
- **Health check**: `/health`
- **Domínio**: `clinica.seudominio.com`
- **Variáveis de ambiente**:
  ```
  APP_MODE=both
  DATABASE_URL=postgresql+asyncpg://medico:SENHA@$(PROJECT_NAME)_postgres:5432/sistema_medico
  REDIS_URL=redis://$(PROJECT_NAME)_redis:6379/0
  UAZAPI_BASE_URL=https://combustiveldigital.uazapi.com
  UAZAPI_ADMIN_TOKEN=<seu admin token>
  UAZAPI_INSTANCE=clinica
  OPENROUTER_API_KEY=sk-or-v1-...
  SECRETARIA_TELEFONE=5511999999999
  WEBHOOK_SECRET=<gere com openssl rand -base64 24>
  JWT_SECRET=<gere com openssl rand -base64 32>
  TZ=America/Sao_Paulo
  ```
  > Troque `$(PROJECT_NAME)` pelo nome real do seu projeto no EasyPanel (ex: `proxy_postgres`).

### 6. Deploy
Clica em **Deploy**. Ele vai:
- Buildar o frontend (Next.js static export)
- Buildar o backend (FastAPI + worker)
- Rodar migrations (Alembic) na primeira vez
- Subir api + worker + agendador no mesmo processo (`APP_MODE=both`)

### 7. Criar admin (primeiro acesso)
```bash
curl -X POST https://clinica.seudominio.com/api/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"nome":"Dr Fulano","email":"medico@clinica.com","senha":"senha-forte"}'
```

### 8. Conectar WhatsApp
- Logar em `https://clinica.seudominio.com/login`
- Menu **WhatsApp** → **Gerar QR code** → escanear no celular
- Clicar em **Salvar webhook** (URL `https://clinica.seudominio.com/api/webhook` já vem preenchida)

### 9. Configurar agenda
- Menu **Config** → ajustar nome do médico, horários, duração, cadência de lembretes

### 10. Tablet da clínica
- Abrir em modo kiosco: `https://clinica.seudominio.com/checkin`
- Rota não exige login

## Rotas

| Path | Atende |
|---|---|
| `/` | Frontend (redireciona pra `/login` ou `/agenda`) |
| `/login`, `/agenda`, `/pacientes`, etc | Frontend Next.js |
| `/checkin` | Tablet da clínica (kiosco, sem login) |
| `/api/*` | API FastAPI |
| `/api/webhook` | Webhook UazAPI |
| `/health` | Health check (não exige auth) |

## Smoke test

1. `curl https://clinica.../health` → `{"status":"ok"}`
2. Acessar `https://clinica.../` no browser → vai pra `/login`
3. Setup do admin → entrar no painel
4. **WhatsApp** → escanear QR
5. **Pacientes** → **+ Novo paciente** → assinar → agendar
6. Verificar lembrete no banco: `SELECT * FROM lembretes WHERE status='pendente'`

## Local (dev)
```bash
cp .env.example .env
# edita .env
docker compose up -d
# acessa http://localhost:8000
```

## Alternativa: separar serviços (escala)
Em produção com tráfego alto vale separar:
- App `api` (`APP_MODE=api`)
- App `worker` (`APP_MODE=worker`)
- App `frontend` separado (Nginx servindo static)

Mas pra o MVP da clínica, 1 App resolve.
