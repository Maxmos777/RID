# Contributing — RID Platform

Guia de contribuição para o projecto RID Platform. Segue a metodologia **Ring** (skills + agentes) e o processo de governance **PMI/PMBOK 8th Edition**.

---

## Antes de começar

1. Ler o [Project Charter](pmo/initiation/project-charter.md) para entender o escopo
2. Ler os [ADRs](docs/adr/README.md) — especialmente ADR-001 e ADR-002 (P0)
3. Correr `make dev-setup` para configurar o ambiente local

---

## Fluxo de desenvolvimento

```
Ideia/Bug
    │
    ▼
Gate 3.5: Verificar ADR existente?
    │ Sim → referenciar no PR
    │ Não → criar novo ADR antes do merge
    ▼
Implementação (ring:dev-cycle)
    │
    ▼
Testes verdes + lint clean
    │
    ▼
PR com ADR Impact checklist
    │
    ▼
Code Review (ring:codereview)
    │
    ▼
Merge
```

---

## Gate 3.5 — ADR Compliance (OBRIGATÓRIO)

Antes de qualquer PR em ficheiros críticos, verificar se existe ADR cobrindo a mudança:

```bash
# Audit de ADRs via testes pytest (não existe script bash — ver ADR-001 a ADR-006)
cd backend && pytest tests/test_architecture.py -v
# Expected: 15 passed
```

**Ficheiros que requerem verificação ADR:**

| Ficheiro / Pasta | ADR relevante |
|---|---|
| `backend/api/deps.py` | ADR-001 (sync_to_async) |
| `backend/core/settings.py` — SHARED_APPS/TENANT_APPS | ADR-002 (users schema público) |
| `backend/core/asgi.py` | ADR-003 (ASGI híbrido) |
| `backend/apps/tenants/services.py` | ADR-004 (service layer) |
| `backend/core/auth_backends.py` | ADR-005 (TenantAwareBackend) |
| `docker-compose.yml` — portas | ADR-006 (porta 5433) |
| `backend/apps/*/models.py` | ADR-002 se adicionar utilizadores |

---

## PR Checklist — ADR Impact

Incluir em **todos os PRs** que modifiquem ficheiros críticos:

```markdown
## ADR Impact

- [ ] Coberto por ADR existente: **ADR-{NNN}** — _{título}_
- [ ] Requer novo ADR antes de merge: **ADR-{NNN}** — _{título proposto}_
- [ ] Não requer ADR (motivo: _______________)

## Verificações

- [ ] `make test` passa (7+ testes)
- [ ] `make lint` passa (ruff clean)
- [ ] `pytest tests/test_architecture.py` — 15 passed (audit de ADRs)
- [ ] `CONTRIBUTING.md` atualizado se novo padrão introduzido
- [ ] `pmo/delivery/change-log.md` atualizado
```

---

## Comandos essenciais

```bash
# Setup inicial
make dev-setup       # instala deps + configura .env

# Desenvolvimento
make up              # sobe PostgreSQL + Redis via Docker
make test            # corre pytest
make lint            # ruff check

# Migrações
make migrate-up      # aplica migrações pendentes
make migrate-create  # cria nova migração

# ADR audit (via pytest, não script bash)
cd backend && pytest tests/test_architecture.py -v

# Parar ambiente
make down            # para e remove containers
```

---

## Criação de ADRs

Quando introduzires uma decisão arquitectural:

1. Copiar `docs/adr/TEMPLATE.md` → `docs/adr/ADR-{NNN}-{slug}.md`
2. Preencher todas as 8 secções (sem `TODO` ou `TBD`)
3. Estado inicial: `Proposed`
4. Submeter no mesmo PR que o código
5. Após revisão: actualizar para `Accepted` + actualizar `docs/adr/README.md`

**Triagem de prioridade ADR:**

| Critério | Prioridade |
|---|---|
| Afecta isolamento de tenant (`set_tenant`, `schema`, `connection`) | P0 — bloqueia merge |
| Afecta autenticação / autorização | P0 — bloqueia merge |
| Afecta arquitectura de processo (ASGI, workers, async) | P1 — resolver em 48h |
| Afecta service layer ou padrão de negócio | P1 — resolver em 48h |
| Afecta integração externa (SSO, Stripe, Langflow) | P2 — antes do gate |
| Afecta ambiente de desenvolvimento / Docker | P3 — pode ir no PR seguinte |

---

## Tecnologias e convenções

| Área | Padrão |
|---|---|
| Python | `uv` para gestão de deps; `ruff` para lint |
| Async Django | `sync_to_async(thread_sensitive=True)` (ver ADR-001) |
| Novos modelos de utilizador | Sempre em `SHARED_APPS` (ver ADR-002) |
| Novas rotas API | Router FastAPI em `api/routers/`; usar `TenantSchema` dependency |
| Testes | `pytest-asyncio` + `@pytest.mark.django_db(transaction=True)` para testes async com BD |
| Commits | Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:` |

---

## Recursos

- [ADRs](docs/adr/README.md) — decisões arquitecturais
- [Plano de Arquitectura](docs/plans/2026-04-03-rid-platform-architecture.md)
- [Risk Register](pmo/docs/03-risk-register.md)
- [Change Log](pmo/docs/05-change-log.md)
- [Ring Skills](https://github.com/lerianstudio/ring) — framework de desenvolvimento

---

*Governance: PMBOK 7 (PMI) | Processo: Ring dev-cycle | Revisão: cada End Stage Assessment*
