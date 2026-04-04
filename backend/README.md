# Backend — RID Platform

Django 6 + FastAPI num processo ASGI único, com `django-tenants` para isolamento por schema PostgreSQL.

---

## Setup local

```bash
# Pré-requisitos: uv, Docker

# 1. Subir PostgreSQL + Redis
cd /home/RID && docker compose up db redis -d

# 2. Criar e activar ambiente virtual
cd /home/RID/backend
uv venv .venv && . .venv/bin/activate

# 3. Instalar dependências
uv sync

# 4. Copiar .env de exemplo
cp .env.example .env   # editar se necessário (porta DB = 5433)

# 5. Aplicar migrações
python manage.py migrate --run-syncdb

# 6. Correr testes
pytest -v

# 7. Iniciar servidor
uvicorn core.asgi:application --reload --port 8000
```

**API:** `http://localhost:8000/api/health` → `{"status": "ok"}`
**Admin Django:** `http://localhost:8000/admin/`

---
## SPA — RockItDown (entrypoint)

Com **`DEBUG=True`**, o projecto define `SHOW_PUBLIC_IF_NO_TENANT_FOUND` e `PUBLIC_SCHEMA_URLCONF`, para que pedidos a **`http://localhost:8000`** (sem `Domain` para `localhost`) usem o schema **public** e `/app/` não falhe com 404 de tenant.

Em produção (`DEBUG=False`), cada hostname de cliente deve existir em `tenants_domain` (ex.: `{schema}.rid.localhost`).

O entrypoint do SPA é servido pelo Django em:
- `GET /app/` → `apps.accounts.views.RockItDownSPA` (requer login via `LoginRequiredMixin`)

A view injeta no HTML inicial um blob JSON `app_config_json` com:
- `tenant.schema_name`
- `api.base_url` e `api.langflow_auto_login_url`
- `csrf_token` para o frontend fazer chamadas autenticadas/CSRF-protected

Os bundles do SPA são gerados no frontend (Vite) e copiados para:
- `backend/static/apps/rockitdown/assets/`

Comando (Phase 4 — Frontend Monorepo):
```bash
cd /home/RID/frontend
pnpm --filter @rid/rockitdown build
```

Observação: o `index.html` continua sendo servido como **template Django** (não como arquivo estático do Vite).
---

## Estrutura de apps

```
backend/
├── api/
│   ├── main.py            ← FastAPI app factory (create_app)
│   ├── deps.py            ← dependency get_current_tenant (sync_to_async — ADR-001)
│   ├── langflow_mixin.py  ← BaseLangflowMixin (placeholder)
│   └── routers/
│       └── langflow.py    ← router placeholder /langflow/health
├── apps/
│   ├── tenants/           ← Customer, Domain, provision_tenant_for_user (ADR-004)
│   └── accounts/          ← TenantUser (schema público — ADR-002), TenantMembership
├── core/
│   ├── asgi.py            ← dispatcher Django/FastAPI (ADR-003)
│   ├── settings.py        ← SHARED_APPS/TENANT_APPS, AUTHENTICATION_BACKENDS
│   ├── auth_backends.py   ← TenantAwareBackend user@tenant (ADR-005)
│   └── adapters.py        ← TenantAwareAccountAdapter (signup session bus)
├── helpers/
│   ├── billing.py         ← Stripe wrapper com guard sk_test
│   └── utils.py           ← retry_on_rate_limit, download_to_local
└── tests/
    ├── conftest.py        ← fixtures ASGI (AsyncClient + ASGITransport)
    ├── test_architecture.py ← 15 testes ADR compliance (ADR-001 a ADR-006)
    ├── test_deps.py       ← validação Host header (400/404)
    └── test_health.py     ← health endpoint + routing FastAPI vs Django
```

---

## Base de dados

PostgreSQL 16 via Docker na porta **5433** do host (ADR-006 — evita conflito com instância local na 5432).

```env
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=rid
DATABASE_USER=rid
DATABASE_PASSWORD=rid
```

O django-tenants cria um schema PostgreSQL por tenant. Utilizadores ficam no schema `public` (ADR-002).

---

## Comandos úteis

```bash
# Testes
pytest -v                          # suite completa (22 testes)
pytest tests/test_architecture.py  # audit de ADRs (15 testes)

# Lint
ruff check .                       # All checks passed = OK

# Migrações
python manage.py makemigrations
python manage.py migrate

# Shell Django
python manage.py shell

# Criar superuser
python manage.py createsuperuser
```

---

## Decisões arquitecturais relevantes

| ADR | Decisão | Ficheiro |
|---|---|---|
| ADR-001 | `sync_to_async(thread_sensitive=True)` para tenant isolation em FastAPI | `api/deps.py:69` |
| ADR-002 | Utilizadores no schema público (SHARED_APPS) | `core/settings.py:25-47` |
| ADR-003 | Django + FastAPI ASGI híbrido com `_API_PREFIX` routing | `core/asgi.py:35` |
| ADR-004 | `provision_tenant_for_user` idempotente (get_or_create) | `apps/tenants/services.py` |
| ADR-005 | `TenantAwareBackend` — login `user@tenant-domain` | `core/auth_backends.py` |
| ADR-006 | PostgreSQL porta 5433 no Docker | `docker-compose.yml:40` |

Índice completo: [`docs/adr/README.md`](../docs/adr/README.md)

---

## Variáveis de ambiente

Ver `.env.example` para lista completa. Variáveis críticas:

| Variável | Obrigatória em prod | Descrição |
|---|---|---|
| `DJANGO_SECRET_KEY` | Sim | Chave de segurança Django |
| `DATABASE_PASSWORD` | Sim | Senha PostgreSQL |
| `STRIPE_SECRET_KEY` | Sim (`sk_live_*`) | Billing — guard rejeita `sk_test` fora de DEBUG |
| `LANGFLOW_SUPERUSER_PASSWORD` | Sim | Admin Langflow — obrigatório se `DEBUG=False` |
| `REDIS_URL` | Sim | Cache e sessões |
