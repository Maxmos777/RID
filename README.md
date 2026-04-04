# RID Platform

SaaS multi-tenant com integração Langflow AI, Stripe billing e isolamento de dados por schema PostgreSQL.

---

## O que é

O RID Platform permite que organizações criem e usem fluxos de trabalho de IA (via Langflow) sem gerir infraestrutura própria. Cada cliente opera num schema PostgreSQL dedicado, garantindo isolamento de dados.

**Stack:** Python 3.12 · Django 6 · FastAPI · django-tenants · PostgreSQL 16 · Redis 7 · Langflow · React 18 · Stripe

---

## Git (repositório local)

O repositório usa `.gitignore` na raiz para `.env`, `node_modules/`, `.venv/`, caches de pytest/ruff, etc.

Após `git clone`, configure a identidade **neste repositório** (não commite credenciais):

```bash
cd RID
git config --local user.name "O teu nome"
git config --local user.email "teu-email@exemplo.com"
```

Branch por defeito: `main`.

## Início rápido

```bash
# 1. Clonar e entrar na pasta
git clone <repo> && cd RID

# 2. Subir serviços (PostgreSQL + Redis)
make up

# 3. Setup do backend
cd backend && make dev-setup

# 4. Aplicar migrações
make migrate-up

# 5. Correr testes
make test

# 6. Iniciar servidor de desenvolvimento
cd backend && uvicorn core.asgi:application --reload --port 8000
```

API disponível em `http://localhost:8000/api/health`

---

## Estrutura do projecto

```
RID/
├── backend/          ← Django 6 + FastAPI (Python 3.12, uv)
├── frontend/         ← React 18 + Vite + TypeScript (pnpm workspaces)
├── docker-compose.yml← PostgreSQL 16 + Redis 7 + backend + Langflow
├── Makefile          ← comandos de desenvolvimento (make help)
├── CONTRIBUTING.md   ← processo de contribuição, ADR checklist, Gate 3.5
├── docs/
│   ├── adr/          ← Architectural Decision Records (6 ADRs aceites)
│   └── plans/        ← planos de arquitectura e implementação
└── pmo/              ← artefactos PMO (PMBOK 8th Performance Domains)
```

---

## Documentação

| Documento | O que encontras |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Processo de contribuição, PR checklist, Gate 3.5, DoD |
| [`docs/adr/README.md`](docs/adr/README.md) | ADRs — decisões arquitecturais aceites |
| [`pmo/README.md`](pmo/README.md) | PMO — governance, milestones, RAID |
| [`backend/README.md`](backend/README.md) | Setup do backend, estrutura de apps, testes |
| [`docs/plans/`](docs/plans/) | Planos de arquitectura e implementação |

---

## Estado actual

**Gate 4 concluído** — ADRs 6/6 Accepted, PMO estabelecido, 22 testes passados.

**Próximo:** Gate 5 — Production Readiness Audit (`ring:production-readiness-audit`)

---

## Requisitos

- Python 3.12+ com [`uv`](https://github.com/astral-sh/uv)
- Docker + Docker Compose
- Node.js 20+ com [`pnpm`](https://pnpm.io) (para o frontend)
