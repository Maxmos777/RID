# Registo de Decisões (Decision Log)

**Projecto:** RID Platform
**Data:** 2026-04-03
**Versão:** 1.0

---

## Sobre este registo

Este documento actua como **índice central de decisões** do projecto. As decisões arquitecturais formais estão documentadas como ADRs em `docs/adr/`. Decisões de gestão e processo ficam aqui.

---

## Decisões Arquitecturais (ADRs)

*Documentadas formalmente em `docs/adr/`. Ver `docs/adr/README.md` para o índice completo.*

| ADR | Decisão resumida | Estado | Data |
|---|---|---|---|
| [ADR-001](../../docs/adr/ADR-001-sync-to-async-tenant-isolation.md) | `sync_to_async(thread_sensitive=True)` para isolamento de tenant em FastAPI async | ✅ Accepted | 2026-04-03 |
| [ADR-002](../../docs/adr/ADR-002-users-in-public-schema.md) | Utilizadores no schema público (SHARED_APPS), não no schema do tenant | ✅ Accepted | 2026-04-03 |
| [ADR-003](../../docs/adr/ADR-003-django-fastapi-hybrid-asgi.md) | Arquitectura híbrida Django + FastAPI via ASGI num mesmo processo | ✅ Accepted | 2026-04-03 |
| [ADR-004](../../docs/adr/ADR-004-idempotent-service-layer-provisioning.md) | `provision_tenant_for_user` como service layer idempotente | ✅ Accepted | 2026-04-03 |
| [ADR-005](../../docs/adr/ADR-005-tenant-aware-auth-backend.md) | `TenantAwareBackend` com formato de login `user@tenant-domain` | ✅ Accepted | 2026-04-03 |
| [ADR-006](../../docs/adr/ADR-006-postgres-port-5433-docker.md) | PostgreSQL na porta 5433 via Docker (evitar conflito com instância local) | ✅ Accepted | 2026-04-03 |

---

## Decisões de Gestão e Processo

| ID | Data | Decisão | Contexto | Decidido por | Alternativas consideradas |
|---|---|---|---|---|---|
| **DM-001** | 2026-04-03 | Adoptar Ring (skills + agentes) como framework de desenvolvimento | Necessidade de estrutura e qualidade consistentes sem overhead manual | Tech Lead | Processo ad-hoc sem framework; uso apenas de linting |
| **DM-002** | 2026-04-03 | Usar MADR (Markdown Architectural Decision Records) como formato de ADR | Formato leve, em Markdown, compatível com Git, sem ferramentas externas | ring:governance-specialist | RFC (Request for Comments); LADR; Confluence pages |
| **DM-003** | 2026-04-03 | Criar `pmo/docs/` separado de `docs/` para artefactos de gestão | Separação semântica clara entre documentação de engenharia e de gestão | Tech Lead + PMO | Tudo em `docs/`; usar wiki externa (Confluence, Notion) |
| **DM-004** | 2026-04-03 | Adoptar PMI/PMBOK 7 como referência de governance | Framework reconhecido internacionalmente, princípios-based (não prescritivo) | ring:governance-specialist | PRINCE2; SAFe; Scrum puro |
| **DM-005** | 2026-04-03 | Gate 3.5 obrigatório (ADR compliance) entre testes verdes e next feature | Previne drift de decisões críticas ao longo do tempo | ring:governance-specialist | ADR review apenas em retrospectivas |

---

## Decisões Pendentes

| ID | Decisão a tomar | Prazo | Impacto se adiada | Responsável |
|---|---|---|---|---|
| **DP-001** | Pinnar versão Langflow no `docker-compose.yml` | Gate 5 | Breaking change silenciosa na integração Langflow | DevOps |
| **DP-002** | Estratégia de deployment (Kubernetes vs Docker Swarm vs PaaS) | Gate 6 | Afecta arquitectura de Helm charts e CI/CD | Tech Lead + DevOps |
| **DP-003** | Política de retenção de dados por tenant após churn | Gate 6 | Compliance GDPR e custos de armazenamento | Product Owner + Tech Lead |
| **DP-004** | Estratégia SSO / SAML para enterprise tenants | Roadmap futuro | Afecta `TenantAwareBackend` (ADR-005) | Product Owner |

---

## Como usar este log

1. **Nova decisão arquitectural** → criar ADR em `docs/adr/` e adicionar linha na tabela "Decisões Arquitecturais" acima
2. **Nova decisão de gestão/processo** → adicionar linha na tabela "Decisões de Gestão e Processo"
3. **Decisão pendente resolvida** → mover de "Pendentes" para a tabela correcta com estado final
4. **Decisão superseded** → actualizar a linha original com `~~texto~~` e referência à nova decisão

---

*Referência: PMBOK 7, Secção 4.6 — Perform Integrated Change Control; ISO 21500:2021 Sec. 4.3.7*
