# Registo de Riscos — RAID Log

**Projecto:** RID Platform
**Data:** 2026-04-03
**Versão:** 1.0
**Metodologia:** RAID (Risks, Assumptions, Issues, Dependencies)

---

## R — Riscos

| ID | Risco | Categoria | Probabilidade | Impacto | Score | Estado | Resposta | ADR/Ref |
|---|---|---|---|---|---|---|---|---|
| **R1** | Race condition silenciosa em `set_tenant` se `sync_to_async` for removido ou alterado sem `thread_sensitive=True` | Técnico — Segurança de Dados | Baixa | Crítico | **8** | ✅ Mitigado | ADR-001 implementado; `grep` de compliance no `docs/adr/README.md` | ADR-001 |
| **R2** | Drift de ADRs: PR futuro introduz padrão divergente sem referência a ADR | Processo — Governance | Baixa | Alto | **6** | ✅ Mitigado | CONTRIBUTING.md com PR checklist criado; `tests/test_architecture.py` como gate automático | ADR governance plan |
| **R3** | API do Langflow instável entre versões | Técnico — Dependência Externa | Baixa | Médio | **4** | ✅ Mitigado | `langflowai/langflow:1.8.3` pinnado em `docker-compose.yml` (2026-04-03) | ADR-003 |
| **R4** | Chave Stripe de teste (`sk_test_*`) usada em produção inadvertidamente | Técnico — Financeiro | Baixa | Crítico | **7** | ✅ Mitigado | Guard implementado em `helpers/billing.py`; levanta `ValueError` se `DEBUG=False` e chave de teste | helpers/billing.py |
| **R5** | Schema PostgreSQL em estado inconsistente após crash durante provisionamento | Técnico — Dados | Baixa | Alto | **6** | ✅ Mitigado | `provision_tenant_for_user` idempotente via `get_or_create`; re-executável sem efeito colateral | ADR-004 |
| **R6** | Utilizadores movidos para schema do tenant por engenheiro sem contexto de ADR-002 | Processo — Arquitectura | Baixa | Crítico | **7** | ✅ Mitigado | ADR-002 Accepted; `test_adr002_accounts_not_in_tenant_apps` como guard automático; PR checklist activo | ADR-002 |
| **R7** | `django-tenants` incompatível com futuras versões do Django (upgrade path) | Técnico — Dependência | Baixa | Alto | **5** | 🔴 Monitorizar | Verificar compatibilidade em cada upgrade major do Django; `django-tenants` mantido activamente | — |
| **R8** | Segredo `LANGFLOW_SUPERUSER_PASSWORD` não configurado em produção | Técnico — Segurança | Média | Alto | **8** | ✅ Mitigado | `settings.py` levanta `ImproperlyConfigured` se `DEBUG=False` e password ausente | core/settings.py |

**Score = Probabilidade × Impacto** (1=Baixa/Baixo, 2=Média/Médio, 3=Alta/Alto, C=Crítico×3)

---

## A — Suposições (Assumptions)

| ID | Suposição | Impacto se Falsa | Validação Prevista |
|---|---|---|---|
| **A1** | `django-tenants` é compatível com django-allauth v65+ sem patches | Fluxo de signup quebra (allauth usa schema público, tenants usa schema do tenant) | Testado em M1 — allauth funciona no schema público ✅ |
| **A2** | A imagem Docker `langflowai/langflow:latest` mantém a API de auto-login estável | Bridge Langflow quebra em actualizações silenciosas | Pinnar versão antes de Gate 5 |
| **A3** | PostgreSQL 16 é compatível com `django-tenants` e o backend `postgresql_backend` | Migrações automáticas de schema podem falhar | Testado localmente com PG 16 ✅ |
| **A4** | A chave Stripe de produção (`sk_live_*`) será fornecida antes do Gate 5 (deployment) | Billing não funcional em staging | Dependência do Product Owner (S1) |
| **A5** | Redis 7 suporta todas as operações de cache e sessões usadas pelo Django | Sessões perdidas em restart do Redis sem persistência configurada | Redis com `--save 60 1` no docker-compose ✅ |

---

## I — Issues (Problemas em Aberto)

| ID | Issue | Prioridade | Estado | Responsável | Prazo |
|---|---|---|---|---|---|
| **I1** | `CONTRIBUTING.md` não existe — PR checklist ADR Impact não estava activo | Alta | ✅ Resolvido | Tech Lead | 2026-04-03 |
| **I2** | `scripts/audit-adrs.sh` referenciado mas não existe — audit substituído por pytest | Média | ✅ Resolvido | Engenheiro | 2026-04-03 |
| **I3** | Langflow sem pin de versão (`latest`) no `docker-compose.yml` | Média | ✅ Resolvido | DevOps | 2026-04-03 |
| **I4** | `backend/README.md` vazio — onboarding de novo engenheiro impossível | Alta | ✅ Resolvido | Tech Lead | 2026-04-03 |
| **I5** | Aviso de teardown de test database no pytest (`OperationalError`) | Baixa | 🟡 Monitorizar | Engenheiro Backend | Gate 5 |
| **I6** | `thread_sensitive=True` em `sync_to_async` — contenção sob carga; sem nota de performance | Média | 🔴 Aberto | Eng. Backend | Gate 5 |
| **I7** | Gate 3.5 sem exceções para hotfix/security — falta SLA de dispensa definido | Média | 🔴 Aberto | Tech Lead | Gate 5 |
| **I8** | Health check não distingue liveness vs readiness com dependências externas (Postgres, Redis) | Média | 🔴 Aberto | SRE | Gate 5 |
| **I9** | Logging JSON sem correlação (request-id/trace-id) | Média | 🔴 Aberto | Eng. Backend | Gate 5 |
| **I10** | SLOs/SLIs e error budget não definidos | Alta | 🔴 Aberto | SRE | Gate 5 |
| **I11** | Baseline de alertas com on-call e runbooks ausente | Alta | 🔴 Aberto | SRE | Gate 5 |
| **I12** | KPIs de produto (conversão, time-to-value, churn) não definidos | Média | 🔴 Aberto | Produto | Gate 6 |
| **I13** | Plano de user research e critérios de aceitação de produto ausentes | Média | 🔴 Aberto | Produto | Gate 6 |

---

## D — Dependências (Dependencies)

| ID | Dependência | Tipo | Projecto/Equipa | Estado | Impacto no Schedule |
|---|---|---|---|---|---|
| **D1** | Chave Stripe de produção | Externa | Product Owner / Finance | ⬜ Pendente | Bloqueia Gate 5 (billing em staging) |
| **D2** | Domínio de produção e certificado SSL/TLS | Externa | DevOps / Infra | ⬜ Pendente | Bloqueia Gate 6 (deployment) |
| **D3** | Langflow versão estável com API documentada | Externa — Open Source | LangChain Inc. | ✅ `1.8.3` pinnada | Phase 5 desbloqueada (actualizar com teste) |
| **D4** | Aprovação do schema de base de dados por DBA / Tech Lead | Interna | Tech Lead | ✅ Implícita (migrations aplicadas) | N/A |
| **D5** | Frontend monorepo setup (pnpm, Node.js) | Interna | Engenheiro Frontend | ⬜ Pendente | Bloqueia Phase 4 (Frontend Bootstrap) |

---

## Histórico de Actualizações

| Versão | Data | Alteração | Gate |
|---|---|---|---|
| 1.0 | 2026-04-03 | Versão inicial — 8 riscos, 5 suposições, 5 issues, 5 dependências | Gate 4 |
| 1.1 | 2026-04-03 | Brainstorm multi-equipa: R2/R3/R6 mitigados; I1–I4 resolvidos; I6–I13 adicionados (Eng+SRE+Produto); D3 mitigada | Gate 4 |

---

## Próxima Revisão

**Gate 5** (Production Readiness Audit) — rever todos os items `🔴 Aberto` e `⚠️ Parcialmente mitigado`.

---

*Referência: PMBOK 7, Secção 11 — Risk Management; PRINCE2 — Risk Register*
