# Cronograma de Milestones — RID Platform

**Data:** 2026-04-03
**Estado:** Schedule Baseline Activa
**Versão:** 1.0
**Fundamento:**
- *Scheduling Practice Standard 3rd Ed.* §4 — Schedule Baseline
- *PMBOK 8th Ed.* §2.6 — Planning Performance Domain
- *OPM Standard Vol. 1* §5.3 — Programme Scheduling

---

## Linha de Base de Milestones

| Marco | Descrição | Gate | Estado | Data |
|---|---|---|---|---|
| **M0** | Projecto iniciado, arquitectura base definida | Gate 0–1 | ✅ | 2026-04-03 |
| **M1** | Backend Foundation (Django + FastAPI + multi-tenant + testes verdes) | Gate 3 | ✅ | 2026-04-03 |
| **M1.5** | ADR Governance (6/6 Accepted) + PMO estabelecido | Gate 4 | ✅ | 2026-04-03 |
| **M2** | FastAPI API Layer (Langflow bridge, tenant middleware, routers) | Gate 5 | ⬜ | TBD |
| **M3** | Frontend Bootstrap (React 18, pnpm workspaces, Vite, TypeScript) | Gate 5 | ⬜ | TBD |
| **M4** | Langflow Integration (Docker, auto-login, workspace por tenant) | Gate 5 | ⬜ | TBD |
| **M5** | Auth + Billing (Allauth completo, Stripe checkout, subscrições) | Gate 5 | ⬜ | TBD |
| **M6** | MVP Deployment (Nginx, HTTPS, staging environment) | Gate 6 | ⬜ | TBD |

---

## Gate × Milestone Map

```
Gate 0–1  ── Initiation + Planning        ✅  → M0
Gate 2–3  ── Foundation + Tests           ✅  → M1
Gate 4    ── ADR Governance + PMO         ✅  → M1.5
Gate 5    ── Production Readiness         ⬜  → M2 ∧ M3 ∧ M4 ∧ M5
Gate 6    ── First Feature Cycle          ⬜  → M6
```

---

## Critical Path para Gate 5

```
M1.5 (concluído)
    │
    ├── [CRÍTICO] M2 — FastAPI API Layer
    │     └── pré-req: Tasks 8+9 code-review-fixes.md concluídas
    │     └── output: OpenAPI spec em /api/docs
    │     └── duração estimada: 4–6h
    │
    ├── M4 — Langflow Integration          [depende de M2]
    │     └── pré-req: M2 + D3 resolvido (Langflow version pin)
    │     └── duração estimada: 6–8h
    │
    ├── M5 — Auth + Billing               [paralelo com M4]
    │     └── pré-req: D1 desbloqueado (Stripe sk_live)
    │     └── duração estimada: 4–6h
    │
    └── M3 — Frontend Bootstrap           [paralelo, depende de M2 spec]
          └── pré-req: OpenAPI spec de M2 + D5 (pnpm setup)
          └── duração estimada: 4–6h

Gate 5 = M2 ∧ M3 ∧ M4 ∧ M5 ∧ Production Readiness Audit (ring:production-readiness-audit)
```

---

## Dependências Externas

| ID | Dependência | Bloqueia | Estado | Responsável |
|---|---|---|---|---|
| D1 | Chave Stripe de produção (`sk_live_*`) | M5, Gate 5 | ⬜ Pendente | Product Owner |
| D2 | Domínio de produção + SSL/TLS | M6, Gate 6 | ⬜ Pendente | DevOps / Infra |
| D3 | Langflow versão pinnada (sem `:latest`) | M4 | ⚠️ Risco activo | DevOps |
| D5 | Frontend setup (pnpm, Node.js, Vite) | M3 | ⬜ Pendente | Eng. Frontend |

---

## Pré-condições para Gate 5

| Condição | Estado | Bloqueante? |
|---|---|---|
| M2 concluído (FastAPI API Layer + OpenAPI spec) | ⬜ | Sim |
| D1 desbloqueado (Stripe `sk_live_*`) | ⬜ | Sim |
| D3 resolvido (Langflow versão pinnada) | ⚠️ | Não (mas risco activo) |
| I1: `CONTRIBUTING.md` com PR checklist | ⬜ | Não (risco de drift) |
| I4: `backend/README.md` com setup guide | ⬜ | Não (bloqueia onboarding) |
| Software Lifecycle Baseline `Accepted` | ✅ | Sim |
| Gate 4 End Stage Assessment criado | ✅ | Sim |

---

## Histórico de Revisões

| Versão | Data | Alteração | Gate |
|---|---|---|---|
| 1.0 | 2026-04-03 | Versão inicial — baseline pós Gate 4 | Gate 4 |

---

*Fundamento: Scheduling Practice Standard 3rd §4; PMBOK 8th §2.6 Planning Domain; OPM Standard Vol. 1 §5.3*
