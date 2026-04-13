# Termo de Abertura do Projecto (Project Charter)

**Projecto:** RID Platform
**Data de início:** 2026-04-03
**Estado:** Activo — Fase de Fundação
**Versão:** 1.0

---

## 1. Finalidade e Justificativa de Negócio

O RID Platform é uma plataforma SaaS multi-tenant que permite a organizações criarem e gerirem fluxos de trabalho de Inteligência Artificial (via Langflow) de forma isolada, segura e escalável. Cada cliente (tenant) opera num ambiente PostgreSQL dedicado (schema-per-tenant), garantindo isolamento de dados e conformidade regulatória.

**Problema que resolve:**
- Equipas sem infraestrutura técnica necessitam de aceder a fluxos LLM sem gerir infra própria.
- Operadores precisam de onboarding automatizado por tenant, sem intervenção manual por cliente.

**Valor de negócio:**
- Modelo SaaS com billing por plano (Free / Basic / Pro / Enterprise via Stripe).
- Time-to-value para o cliente: signup → Langflow funcional em < 5 minutos.

---

## 2. Descrição do Produto

### Componentes principais

| Componente | Tecnologia | Responsabilidade |
|---|---|---|
| Backend API | Django 6 + FastAPI (Python 3.12) | Auth, multi-tenancy, billing, Langflow bridge |
| Base de dados | PostgreSQL 16 (schema-per-tenant) | Isolamento de dados por cliente |
| Cache / Pub-Sub | Redis 7 | Sessões, cache, filas futuras |
| AI Workflows | Langflow (Docker) | Motor de fluxos LLM por tenant |
| Frontend | React 18 + Vite + TypeScript | SPA principal + embed Langflow |
| Billing | Stripe | Subscrições e pagamentos |
| Infraestrutura | Docker Compose → Kubernetes (futuro) | Ambiente local e produção |

### Arquitetura de alto nível

```
Utilizador
    │
    ▼
Nginx (reverse proxy)
    ├── /             → Django (templates, admin, allauth)
    ├── /api/*        → FastAPI (REST, Langflow bridge)
    └── /langflow/*   → Langflow (Docker container)

PostgreSQL (schema-per-tenant)
    ├── public         → TenantUser, TenantMembership, Customer, Domain
    └── {schema_name}  → dados de negócio por tenant
```

---

## 3. Objetivos e Critérios de Sucesso

| Objetivo | Critério de Sucesso | Prioridade |
|---|---|---|
| Onboarding multi-tenant funcional | Signup → tenant provisionado → Langflow acessível < 5 min | MUST |
| Isolamento de dados garantido | Queries entre tenants impossíveis por construção (schema PostgreSQL) | MUST |
| Billing operacional | Stripe checkout → subscrição activa → acesso por plano | SHOULD |
| Frontend SPA | React app servida pelo Django com hot-reload em dev | SHOULD |
| Production-ready | OWASP Top 10 coberto, HTTPS, variáveis de ambiente sem segredos | COULD |

---

## 4. Escopo do Projecto

### Incluído

- Backend Django + FastAPI com multi-tenancy schema-per-tenant
- Sistema de auth via django-allauth (email, signup, confirmação)
- Provisionamento automático de tenant após signup
- Bridge Langflow por tenant (auto-login, workspace isolado)
- Frontend React SPA (main app + embed Langflow)
- Billing Stripe (checkout, subscrições, cancelamento)
- Infraestrutura Docker Compose para desenvolvimento local
- Documentação de arquitectura (ADRs, planos, PMO)

### Excluído desta fase

- Aplicação mobile
- Integração SSO / SAML / OAuth (planeada em fase futura)
- Infraestrutura Kubernetes / Helm (planeada após MVP)
- Analytics e telemetria avançada (Prometheus/Grafana — Gate 5)
- Multi-região / disaster recovery

---

## 5. Principais Marcos (Milestones)

| Marco | Descrição | Estado |
|---|---|---|
| **M1** — Backend Foundation | Django + FastAPI + multi-tenant + ADRs | ✅ Concluído (2026-04-03) |
| **M2** — FastAPI API Layer | Langflow auto-login, tenant middleware, routers | ⬜ Pendente |
| **M3** — Frontend Bootstrap | React SPA, pnpm workspaces, Vite | ⬜ Pendente |
| **M4** — Langflow Integration | Docker, auto-login, workspace por tenant | ⬜ Pendente |
| **M5** — Auth + Billing | Allauth completo, Stripe checkout | ⬜ Pendente |
| **M6** — MVP Deployment | Nginx, HTTPS, staging environment | ⬜ Pendente |

---

## 6. Restrições e Premissas

### Restrições

| Restrição | Impacto |
|---|---|
| Python 3.12 via `uv` (não `pip` directo) | Gestão de dependências deve usar `uv add` |
| PostgreSQL obrigatório (não SQLite) | `django-tenants` requer backend PostgreSQL |
| `django-tenants` exige utilizadores no schema público | ADR-002 — não alterar sem novo ADR |
| FastAPI apenas em `/api/*` | ADR-003 — Django serve tudo o resto |

### Premissas

- A chave Stripe de produção (`sk_live_*`) será fornecida antes do Gate 5.
- O domínio de produção e certificado SSL serão configurados antes do deployment.
- A imagem Docker do Langflow é gerida externamente (`langflowai/langflow:latest`).

---

## 7. Riscos de Alto Nível

*Ver detalhe completo em `pmo/docs/03-risk-register.md`.*

| ID | Risco | Probabilidade | Impacto |
|---|---|---|---|
| R1 | Race condition em `set_tenant` async | Baixa (mitigada — ADR-001) | Alto |
| R2 | Drift de ADRs por falta de PR checklist | Média | Alto |
| R3 | Langflow API instável entre versões | Média | Médio |
| R4 | Chave Stripe test em produção | Baixa (guard implementado) | Alto |
| R5 | Schema PostgreSQL sem migração após crash | Baixa (idempotência implementada) | Alto |

---

## 8. Partes Interessadas

*Ver detalhe em `pmo/docs/02-stakeholder-register.md`.*

| Papel | Interesse Principal |
|---|---|
| Product Owner | Funcionalidades de valor para o cliente final |
| Tech Lead | Qualidade arquitectural, ADRs, decisões técnicas |
| Engenheiro Backend | Implementação, testes, migrations |
| Engenheiro Frontend | SPA, integração com API |
| Operações / DevOps | Docker, deployment, observabilidade |

---

## 9. Autoridade e Aprovação

**Responsável pelo projecto:** a definir
**Aprovação deste charter:** a definir
**Data de revisão seguinte:** no Gate 5 (Production Readiness Audit)

---

*Referência: PMBOK 7, Secção 4.1 — Develop Project Charter*
