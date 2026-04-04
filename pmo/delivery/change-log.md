# Change Log — Registo de Mudanças

**Projecto:** RID Platform
**Data início:** 2026-04-03
**Versão:** 1.0

---

## Sobre este registo

Regista todas as mudanças significativas ao projecto: código, arquitectura, processo e governance. Actualizado em cada gate e em mudanças de impacto.

**Formato de versão:** `MAJOR.MINOR.PATCH`
- `MAJOR` — mudança arquitectural breaking (novo ADR obrigatório)
- `MINOR` — nova funcionalidade ou componente
- `PATCH` — fix, refactoring ou melhoria sem breaking change

---

## [Unreleased]

### A adicionar antes do Gate 5
- `pmo/governance/gate-lifecycle.md` — definições formais de gate
- `pmo/governance/opm-alignment.md` — alinhamento OPM3
- `pmo/performance/metrics-baseline.md` — SPI/CPI, Lead vs Lag
- `pmo/performance/technical-debt-register.md` — dívida técnica formal
- I6–I11 do RAID (SRE: liveness/readiness, correlation, SLOs, alertas)
- `backend/README.md` — nota sobre `thread_sensitive=True` e limites de concorrência

---

## [0.5.0] — 2026-04-03 — Brainstorm multi-equipa + PMO consolidação

### Adicionado
- `README.md` raiz do projecto — início rápido, estrutura, links
- `backend/README.md` — setup, estrutura de apps, comandos, tabela de ADRs
- `pmo/planning/software-lifecycle-baseline.md` — Software Extension 5th: V&V, ciclo de vida, quality gates, SCM, dívida técnica
- `pmo/planning/milestone-schedule.md` — baseline M0–M6, critical path, dependências
- `pmo/governance/contributing-process.md` — PR checklist PMO, DoD, Gate 3.5
- `pmo/performance/gate-reports/gate-04-end-stage-assessment.md` — closure formal Gate 4

### Alterado
- `CONTRIBUTING.md` — PMBOK 8th, links `pmo/initiation/` (era `pmo/docs/`), audit via pytest (era script bash)
- `docker-compose.yml` — Langflow `1.8.3` pinnada (era `:latest` — D3 mitigada)
- `pmo/uncertainty/raid-log.md` v1.1 — R2/R3/R6 mitigados; I1–I4 resolvidos; I6–I13 adicionados
- `pmo/README.md` — referência PMBOK 8th Performance Domains como base estrutural
- Ring `pmo-team/skills/docs/` — 3 novas obras (PMBOK 8th, Software Extension 5th, OPM Vol.1); SKILL.md de 5 skills actualizados

### Removido
- `pmo/docs/` (estrutura antiga PMBOK 7, ficheiros numerados) — substituída por `pmo/initiation/`, `pmo/planning/`, etc.
- `scripts/audit-adrs.sh` — substituído por `backend/tests/test_architecture.py` (15 testes pytest)

### Decisões de gestão adicionadas (DM-006 a DM-008)
- DM-006: Gate 5 mantido como gate hard — nada de produto até audit passar
- DM-007: `pmo/docs/` eliminado — nova árvore `pmo/` por Performance Domains é o cânone
- DM-008: Audit de ADRs via pytest em vez de script bash (regra: sem scripts de compliance soltos)

---

## [0.4.0] — 2026-04-03 — Gate 4: ADR Governance

### Adicionado
- **6 ADRs** em estado `Accepted` em `docs/adr/`:
  - ADR-001: `sync_to_async` isolamento de tenant
  - ADR-002: utilizadores no schema público
  - ADR-003: Django + FastAPI ASGI híbrido
  - ADR-004: service layer idempotente
  - ADR-005: `TenantAwareBackend`
  - ADR-006: PostgreSQL porta 5433
- `docs/adr/README.md` — índice com score de compliance 6/6 (100%)
- `docs/adr/TEMPLATE.md` — template MADR para ADRs futuros
- `pmo/docs/` — estrutura PMO com semântica PMI/PMBOK 7:
  - `01-project-charter.md`
  - `02-stakeholder-register.md`
  - `03-risk-register.md` (RAID Log)
  - `04-decision-log.md`
  - `05-change-log.md` (este ficheiro)
  - `governance/adr-governance-plan.md`

---

## [0.3.0] — 2026-04-03 — Gate 3: DevOps + Testes Verdes

### Adicionado
- `Dockerfile` multi-stage (builder → production), Python 3.12-slim, non-root user
- `docker-compose.yml` com PostgreSQL 16 + Redis 7 + backend + langflow (profile)
- `backend/.env.example` com todas as variáveis documentadas
- `Makefile` com 17 comandos Ring
- `backend/.dockerignore`
- `pytest.ini` + `tests/conftest.py` + `tests/test_health.py` + `tests/test_deps.py`
- `pytest-asyncio` como dev dependency

### Estado
- 7 testes passados, 0 falhas
- `ruff check .` — All checks passed
- PostgreSQL (porta 5433) e Redis acessíveis e healthy

---

## [0.2.0] — 2026-04-03 — Gate 2: Execução do Code Review Fixes Plan (13 tasks)

### Adicionado
- `api/deps.py` — `sync_to_async` com `thread_sensitive=True` para isolamento de tenant
- `apps/tenants/services.py` — `provision_tenant_for_user` idempotente com `get_or_create`
- `core/auth_backends.py` — `TenantAwareBackend` para login `user@tenant-domain`
- `core/adapters.py` — `TenantAwareAccountAdapter` (session bus para signup allauth)
- `helpers/billing.py` — wrapper Stripe completo com guard `sk_test` em produção
- `helpers/utils.py` — `retry_on_rate_limit`, `download_to_local`, `timestamp_to_datetime`
- `api/langflow_mixin.py` — `BaseLangflowMixin` placeholder para views Langflow
- `api/routers/langflow.py` — router FastAPI placeholder com `/langflow/health`
- `apps/accounts/migrations/0001_fix_invited_by_related_name.py` — migração

### Alterado
- `api/deps.py` — isolamento async + validação host 400 + `select_related("tenant")`
- `core/asgi.py` — `_API_PREFIX` routing cobre `/api` e `/api/*`
- `apps/tenants/signals.py` — thin dispatcher com `threading.Thread`
- `apps/accounts/models.py` — `invited_by` com `related_name="sent_invites"` + property `invited_by_user`
- `core/settings.py` — `AUTHENTICATION_BACKENDS` + `ACCOUNT_ADAPTER`

---

## [0.1.0] — 2026-04-03 — Gate 1: Backend Foundation

### Adicionado
- Django 6 + FastAPI ASGI híbrido (`core/asgi.py`)
- `django-tenants` com schema-per-tenant (PostgreSQL)
- `django-allauth` v65+ com login por email
- Modelos: `Customer`, `Domain`, `TenantUser`, `TenantMembership`
- `apps/tenants/signals.py` — provisionamento de schema após criação de tenant
- `core/settings.py` — `SHARED_APPS` / `TENANT_APPS` separation
- `pyproject.toml` com `uv` como package manager
- `backend/.env` com variáveis de desenvolvimento

### Plano
- `docs/plans/2026-04-03-rid-platform-architecture.md` — plano completo de 7 fases
- `docs/plans/2026-04-03-code-review-fixes.md` v2 — 13 tasks com rationale RockItDown

---

## Formato de entrada (para uso futuro)

```markdown
## [X.Y.Z] — YYYY-MM-DD — Gate N: Descrição

### Adicionado
- Nova funcionalidade ou ficheiro

### Alterado
- Mudança em funcionalidade existente (com referência a ADR se arquitectural)

### Corrigido
- Bug fix com referência a issue

### Removido
- Código ou funcionalidade removida

### Breaking Changes
- ⚠️ Mudança que requer ADR e update de dependentes
```

---

*Baseado em: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) + PMBOK 7 Change Log*
