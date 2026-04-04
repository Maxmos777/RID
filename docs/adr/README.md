# Architectural Decision Records — RID Platform

Este directório contém as decisões arquitecturais formalizadas do projecto RID Platform.
Cada ADR é imutável após `Accepted` — se uma decisão mudar, cria-se um novo ADR
que marca o anterior como `Superseded by ADR-NNN`.

---

## Índice

| ID | Título | Estado | Data | Prioridade | Ficheiro(s) afectado(s) |
|---|---|---|---|---|---|
| [ADR-001](ADR-001-sync-to-async-tenant-isolation.md) | `sync_to_async` com `thread_sensitive=True` para isolamento de tenant em FastAPI async | ✅ Accepted | 2026-04-03 | P0 | `api/deps.py` |
| [ADR-002](ADR-002-users-in-public-schema.md) | Utilizadores no schema público (SHARED\_APPS), não no schema do tenant | ✅ Accepted | 2026-04-03 | P0 | `core/settings.py`, `apps/accounts/` |
| [ADR-003](ADR-003-django-fastapi-hybrid-asgi.md) | Arquitectura híbrida Django + FastAPI via ASGI num mesmo processo | ✅ Accepted | 2026-04-03 | P1 | `core/asgi.py` |
| [ADR-004](ADR-004-idempotent-service-layer-provisioning.md) | `provision_tenant_for_user` como service layer idempotente (não signal directo) | ✅ Accepted | 2026-04-03 | P1 | `apps/tenants/signals.py`, `apps/tenants/services.py` |
| [ADR-005](ADR-005-tenant-aware-auth-backend.md) | `TenantAwareBackend` com formato `user@tenant-domain` | ✅ Accepted | 2026-04-03 | P2 | `core/auth_backends.py` |
| [ADR-006](ADR-006-postgres-port-5433-docker.md) | PostgreSQL na porta 5433 via Docker (evitar conflito com instância local) | ✅ Accepted | 2026-04-03 | P3 | `docker-compose.yml` |
| [ADR-007](ADR-007-frontend-monorepo-pnpm-vite-django-static.md) | Frontend monorepo (pnpm) + Vite → Django static (assets) | 🟡 Proposed | 2026-04-03 | P3 | `frontend/apps/rockitdown/`, `frontend/packages/shared/`, `backend/templates/`, `backend/static/` |
| [ADR-008](ADR-008-langflow-frontend-customization-overlay.md) | Personalização do Frontend Langflow via Customization Overlay + Custom Docker Image | 🟡 Proposed | 2026-04-04 | P2 | `docker-compose.yml`, `langflow-custom/` |
| [ADR-009](ADR-009-langflow-database-integration.md) | Integração Django ↔ Langflow: Base de Dados Partilhada e Multi-tenancy via Workspaces | 🟡 Proposed | 2026-04-04 | P2 | `docker-compose.yml`, `apps/tenants/models.py`, `api/services/langflow_workspace.py` |
| [ADR-010](ADR-010-git-monorepo-root-vendored-ring.md) | Repositório Git na raiz do RID (monorepo) e Ring vendored | ✅ Accepted | 2026-04-04 | P3 | `.gitignore`, `.gitattributes`, `docs/ring-upstream.md`, `README.md` |
| [ADR-011](ADR-011-ring-backend-engineer-python-agent.md) | Agente Ring `ring:backend-engineer-python` e skill Cursor | ✅ Accepted | 2026-04-04 | P3 | `ring/dev-team/agents/backend-engineer-python.md`, `.cursor/skills/backend-engineer-python/` |

**Score de compliance:** 7/11 (64%) — Score P0: 2/2 (✅ COMPLETO). Testes pytest em `test_architecture.py` cobrem ADR-001 a ADR-006 (15 testes) e ADR-009 (4 testes). ADR-007, ADR-008, ADR-010 e ADR-011 ainda não têm testes de compliance automatizados nesse ficheiro (ver secções Compliance em cada ADR).

---

## Lifecycle de estados

```
Proposed ──► Accepted ──► Deprecated
                  │              │
                  └──────────────┴──► Superseded by ADR-NNN
```

| Estado | Emoji | Significado |
|---|---|---|
| Proposed | 🟡 | Rascunho criado, aguarda revisão |
| Accepted | ✅ | Aprovado e em vigor |
| Deprecated | ⚫ | Retirado sem substituto |
| Superseded | 🔁 | Substituído por ADR mais recente |
| Pendente | 🔴 | Identificado mas ainda não escrito |

---

## Como criar um novo ADR

1. Consultar este README e escolher o próximo número sequencial
2. Copiar `docs/adr/TEMPLATE.md` para `docs/adr/ADR-{NNN}-{slug}.md`
3. Preencher todas as 8 secções (nenhuma pode ficar com `TODO` ou `TBD`)
4. Estado inicial: `Proposed`
5. Abrir PR com revisão de pelo menos 1 par
6. Após aprovação: actualizar estado para `Accepted` + actualizar este README
7. Nunca editar um ADR em estado `Accepted` — criar novo e marcar como Superseded

### Convenção de nomes de ficheiro

```
ADR-{NNN}-{slug-kebab-case}.md
```

- `NNN` — 3 dígitos, sequencial, nunca reutilizado (001, 002, ...)
- `slug` — máximo 6 palavras, descreve a decisão (não a tecnologia)
- Sem datas no nome de ficheiro

---

## Triagem de prioridade

| Critério | Prioridade |
|---|---|
| Afecta isolamento de tenant (`set_tenant`, `schema`, `connection`) | P0 |
| Afecta autenticação/autorização | P0 |
| Afecta arquitectura de processo (ASGI, workers, async) | P1 |
| Afecta service layer ou padrão de negócio | P1 |
| Afecta integração externa (SSO, Stripe, Langflow) | P2 |
| Afecta ambiente de desenvolvimento / Docker | P3 |

---

## Auditoria de compliance

As verificações de ADR estão implementadas como **testes pytest** em `backend/tests/test_architecture.py`.
Correm automaticamente em cada `make test` — sem necessidade de execução manual.

```bash
# Correr apenas os testes de arquitectura
cd backend && pytest tests/test_architecture.py -v

# Correr suite completa (inclui arquitectura)
make test
```

**15 testes** cobrem ADR-001 a ADR-006. Qualquer violação falha o suite com mensagem que aponta para o ADR relevante.

Auditoria deve ser verificada em cada **End Stage Assessment** de gate com `make test`.

---

*Governance plan: `pmo/docs/governance/adr-governance-plan.md`*
*RAID Log: `pmo/docs/03-risk-register.md`*
*Decision Log: `pmo/docs/04-decision-log.md`*
