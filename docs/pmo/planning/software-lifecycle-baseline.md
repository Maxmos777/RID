# Software Lifecycle Baseline — RID Platform

**Data:** 2026-04-03
**Estado:** Accepted
**Versão:** 1.0
**Relacionado com:** `pmo/governance/gate-lifecycle.md`, `pmo/initiation/project-charter.md`
**Fundamento:**
- *Software Extension to the PMBOK Guide, 5th Ed.* §3 (Software Life Cycles), §4 (V&V), §5 (Configuration Mgmt), §7 (Planning), §9 (Quality), §11 (Measurements)
- *PMBOK 8th Ed.* — Development Approach & Life Cycle Performance Domain
- *Scheduling Practice Standard 3rd Ed.* §4 — Schedule Baseline

---

## 1. Modelo de Ciclo de Vida Seleccionado

**Modelo:** Adaptive (Iterative-Incremental) com Gates Formais de Governance

### Justificação

| Critério | Avaliação RID Platform |
|---|---|
| Requisitos definidos à partida? | Parcialmente — arquitectura core definida, features evolutivas |
| Tecnologia conhecida? | Sim (Django 6, FastAPI, Langflow) — baixa incerteza técnica |
| Entrega de valor incremental? | Sim — SaaS multi-tenant activa features por tenant |
| Stakeholders disponíveis? | Sim |
| **Modelo seleccionado** | **Adaptive (Iterative-Incremental)** |

### Estrutura de fases

```
Fase 0 — Foundation (Gates 0–4)           ✅ Concluída
    Iteração 0.1: Arquitectura + DevOps (Gates 0–1)
    Iteração 0.2: SRE + Testes (Gates 2–3)
    Iteração 0.3: ADR Governance (Gate 4)

Fase 1 — Core Product (Gates 5–6)         ⬜ Em curso
    Iteração 1.1: Production Readiness (Gate 5)
    Iteração 1.2: First Feature Cycle (Gate 6)

Fase 2 — Growth (Gates 7+)                ⬜ Planeada
    Iterações 2.x: Feature cycles contínuos (ring:dev-cycle Gates 0–9)
```

---

## 2. Definition of Done por Fase

### Fase 0 — Foundation ✅

**Verification** (produto conforme especificações):
- [x] ASGI multi-tenant operacional (`core/asgi.py` + `api/deps.py`)
- [x] 6 ADRs P0/P1/P2/P3 em `Accepted`
- [x] Docker Compose com PostgreSQL 16 + Redis 7 healthy
- [x] 22 testes passados, ruff clean

**Validation** (produto resolve o problema certo):
- [x] Tenant isolation verificada por `tests/test_architecture.py`
- [x] Auth flow `user@tenant-domain` funcional via `TenantAwareBackend`
- [x] Ambiente local reproduzível via `make dev-setup`

---

### Fase 1 — Core Product ⬜

#### Gate 5 — Production Readiness

**Software V&V Checklist** *(Software Extension §4)*

**Verification (técnica):**
- [ ] Production Readiness Audit score ≥ 330/440
- [ ] Zero findings CRITICAL/HIGH de segurança abertas
- [ ] Todas as variáveis de ambiente em `.env.example` documentadas
- [ ] Health check `/api/health` em < 500ms
- [ ] Logging estruturado (JSON) activo em backend
- [ ] Migrations reversíveis (down migrations existem)
- [ ] Rate limiting em endpoints públicos
- [ ] Secrets ausentes de código e logs

**Validation (negócio):**
- [ ] Tenant provisioning testável end-to-end (signup → Langflow funcional)
- [ ] Stripe billing testável em modo test (`sk_test_*`)
- [ ] Disponibilidade ≥ 99.5% verificável em staging

**Software Configuration Baseline (SCM — Software Extension §5):**
- [ ] Dependências Python pinnadas (versões exactas em `requirements.txt`)
- [ ] Imagens Docker com versão explícita (sem `:latest`)
- [ ] Variáveis categorizadas: `SECRET` / `CONFIG` / `FEATURE_FLAG`
- [ ] Git tag `baseline/gate-05` criada após PASS

**Exit criteria:**

| Resultado | Condição |
|---|---|
| PASS | V&V Checklist 100% + Score ≥ 330 + Zero criticals |
| CONDITIONAL PASS | Score 290–329 + plano de remediação com prazo ≤ 5 dias |
| FAIL | Score < 290 OU critical security finding aberta |

---

#### Gate 6 — First Feature Cycle

**Verification:**
- [ ] Feature implementada conforme ADR(s) aprovados
- [ ] Cobertura de testes da feature ≥ 85%
- [ ] Zero regressão nos testes existentes
- [ ] ADR criado se decisão arquitectural nova (Gate 3.5)

**Validation:**
- [ ] Feature testável por utilizador final (smoke test manual)
- [ ] Feature documentada em `pmo/delivery/change-log.md`
- [ ] Tenant isolation mantida pela nova feature

---

## 3. Software Configuration Management (SCM)

*Software Extension §5*

### Itens sob controlo de configuração

| Item | Localização | Responsável de baseline |
|---|---|---|
| Código fonte | `git` branch `main` | Tech Lead |
| Dependências Python | `pyproject.toml` + `requirements.txt` | Eng. Backend |
| Configuração Docker | `docker-compose.yml` | DevOps |
| Variáveis de ambiente | `backend/.env.example` | DevOps |
| Migrações de BD | `apps/*/migrations/` | Eng. responsável |
| ADRs aceites | `docs/adr/` | Tech Lead |
| Schema de API | OpenAPI spec em `/api/docs` (gerado por FastAPI) | Eng. Backend |

### Configuration Baseline por Gate

| Gate | Label | Conteúdo congelado |
|---|---|---|
| Gate 4 | `baseline/gate-04` | ADRs 1–6 Accepted + stack estável |
| Gate 5 | `baseline/gate-05` | Production-ready stack + Langflow integrado |
| Gate 6 | `baseline/gate-06-{feature}` | Feature N entregue + testes verdes |

```bash
# Criar baseline tag após Gate PASS
git tag baseline/gate-05
git push origin baseline/gate-05
```

---

## 4. Quality Gates de Software

*Software Extension §9 + PMBOK 8th Measurement Domain*

```
Q1 — Unit Tests:     pytest com cobertura ≥ 85% (pytest-cov)
Q2 — Linting:        ruff check . — All checks passed
Q3 — Architecture:   pytest tests/test_architecture.py — 15/15 PASS
Q4 — Security:       bandit -r backend/ — sem HIGH/CRITICAL (Gate 5+)
Q5 — Integration:    tenant isolation tests PASS
```

Todos Q1–Q5 são pré-requisito para Gate Assessment (Gate 5+).

---

## 5. Métricas de Qualidade

*Software Extension §11 + PMBOK 8th MMA Catalog*

| Métrica | Fórmula | Target | Frequência | Ferramenta |
|---|---|---|---|---|
| **Test Coverage** | linhas cobertas / linhas totais × 100 | ≥ 85% | Por gate | pytest-cov |
| **ADR Compliance Rate** | ADRs Accepted / ADRs identificados × 100 | 100% P0, ≥ 80% total | Por gate | `docs/adr/README.md` |
| **Change Failure Rate** | deploys com incidente / total deploys × 100 | < 10% | Por iteração | CI/CD logs |
| **Technical Debt Ratio** | tempo remediação estimado / tempo desenvolvimento × 100 | < 5% | Por gate | `performance/technical-debt-register.md` |

### Lead vs Lag Indicators *(PMBOK 8th — distinção nova vs 7th)*

| Tipo | Indicador | Acção |
|---|---|---|
| **Lead** (preditivo) | ADR Compliance Rate em queda | Revisão de PR checklist antes do próximo gate |
| **Lead** (preditivo) | Technical Debt Ratio > 3% | Alocar sprint de remediação |
| **Lead** (preditivo) | Test Coverage < 80% | Bloquear merge de novos features |
| **Lag** (retrospectivo) | Change Failure Rate | Análise post-mortem após iteração |
| **Lag** (retrospectivo) | Gate Assessment score | Comparar com baseline anterior |

---

## 6. Technical Debt Known (Gate 4 Baseline)

*Software Extension §9.4 — Dívida técnica como risco gerível*

| ID | Descrição | Impacto | Prazo | Ref. |
|---|---|---|---|---|
| TD-001 | `TenantAwareBackend` sem testes de integração completos | ALTO | Gate 5 | ADR-005 |
| TD-002 | `tenants/services.py` sem teste end-to-end de provisionamento | MÉDIO | Gate 5 | ADR-004 |
| TD-003 | `backend/README.md` vazio — onboarding impossível | MÉDIO | Imediato | — |
| TD-004 | Dependências sem pins exactas em `pyproject.toml` | MÉDIO | Gate 5 | — |
| TD-005 | Langflow sem pin de versão no `docker-compose.yml` | MÉDIO | Gate 5 | ADR-003 |

Registo completo em `pmo/performance/technical-debt-register.md`.

---

## 7. Estimativa de Esforço

*Software Extension §7.3 — estimativa por analogia*

| Componente | Técnica | Overhead histórico |
|---|---|---|
| Feature nova (Gate 6+) | Story points por analogia com features Gate 4 | ~2–4h por feature simples |
| Remediação de dívida técnica | Time-box: máx 20% da capacidade | TD-001 a TD-005: ~6h total |
| ADR + governance | Fixed overhead por gate | 3h por gate + 45min por ADR |
| Production Readiness Audit | Ring standards (44 dimensões) | 2–4h |

---

## 8. Integração com outros artefactos PMO

```
software-lifecycle-baseline.md    ← define O QUÊ verificar e validar
    │
    ├── pmo/governance/gate-lifecycle.md  ← define QUANDO e QUEM aprova
    ├── pmo/planning/milestone-schedule.md ← define QUANDO cada fase conclui
    ├── pmo/performance/technical-debt-register.md ← regista dívida técnica
    └── docs/adr/README.md               ← rastreia ADR compliance rate
```

**Regra de actualização:** Revisto no início de cada nova Fase. Revisões que afectem critérios de aceitação de gate requerem ADR.

---

*Fundamento: Software Extension to the PMBOK Guide 5th Ed. §3, §4, §5, §7, §9, §11*
*Complementado por: PMBOK 8th Ed. — Development Approach & Life Cycle Domain, Measurement Domain*
