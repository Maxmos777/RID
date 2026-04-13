# PMO — RID Platform

Artefactos de gestão do projecto RID Platform, organizados pelos **Performance Domains do PMBOK 8ª Edição (PMI, 2023)** e pelos **Service Domains do PMO Practice Guide (PMI)**.

---

## Estrutura

```
pmo/
├── initiation/              ← Stakeholders + Development Approach (PMBOK 8th §2.3, §2.5)
│   ├── project-charter.md
│   └── stakeholder-register.md
│
├── planning/                ← Planning Domain (PMBOK 8th §2.6) + Software Extension §3, §7
│   ├── software-lifecycle-baseline.md   ← NOVO: V&V, ciclo de vida, quality gates
│   ├── milestone-schedule.md            ← Baseline M1–M6, caminho crítico
│   └── scope-baseline.md               ← (P1)
│
├── uncertainty/             ← Uncertainty Domain (PMBOK 8th §2.9) + EVM Standard §3
│   └── raid-log.md          ← RAID: Risks, Assumptions, Issues, Dependencies
│
├── decisions/               ← Project Work Domain (PMBOK 8th §2.7) + ISO 21500 §4.3.7
│   └── decision-log.md      ← Decisões arquitecturais (→ ADRs) + gestão
│
├── governance/              ← PMO Practice Guide §4.2 + OPM Standard Vol. 1 §4
│   ├── adr-governance-plan.md
│   ├── contributing-process.md          ← P0: PR checklist, DoD, Gate 3.5
│   ├── opm-alignment.md                 ← P1: alinhamento estratégico OPM3
│   └── gate-lifecycle.md               ← P1: definições formais de gate
│
├── performance/             ← Measurement Domain (PMBOK 8th §2.8) + EVM Standard §4
│   ├── technical-debt-register.md       ← P1: dívida técnica como risco gerível
│   ├── metrics-baseline.md             ← P1: SPI, CPI, Lead vs Lag indicators
│   └── gate-reports/
│       └── gate-04-end-stage-assessment.md  ← P0: closure formal Gate 4
│
└── delivery/                ← Delivery Domain (PMBOK 8th §2.7) + BA Practitioners §5
    └── change-log.md        ← changelog semântico versionado
```

---

## Mapeamento Performance Domains PMBOK 8th → Pastas PMO

| Performance Domain (PMBOK 8th) | Pasta PMO | Artefactos principais |
|---|---|---|
| Stakeholders (§2.3) | `initiation/` | project-charter, stakeholder-register |
| Development Approach & Life Cycle (§2.5) | `initiation/` + `planning/` | project-charter, software-lifecycle-baseline |
| Planning (§2.6) | `planning/` | milestone-schedule, software-lifecycle-baseline, scope-baseline |
| Project Work (§2.7) | `decisions/` + `delivery/` | decision-log, change-log |
| Delivery (§2.7) | `delivery/` | change-log |
| Measurement (§2.8) | `performance/` | metrics-baseline, gate-reports, technical-debt-register |
| Uncertainty (§2.9) | `uncertainty/` | raid-log |
| — | `governance/` | adr-governance-plan, contributing-process, opm-alignment, gate-lifecycle |

> **Nota:** Governance não é um Performance Domain do PMBOK 8th, mas é um **Service Domain** central no PMO Practice Guide (§3.2, §4.2) e no OPM Standard (Vol. 1 §4, Vol. 2 §5).

---

## Gate Lifecycle (definido no ADR Governance Plan)

```
Gate 0  ── Code Review Formal                    ✅ 2026-04-03
Gate 1  ── Plano aprovado, PMO CONDITIONAL PASS  ✅ 2026-04-03
Gate 2  ── Execução 13 tasks + DevOps            ✅ 2026-04-03
Gate 3  ── Testes verdes, lint clean             ✅ 2026-04-03
Gate 4  ── ADRs 6/6 Accepted + PMO estabelecido  ✅ 2026-04-03
Gate 5  ── Production Readiness Audit            ⬜ Próximo
Gate 6  ── First Feature Cycle                   ⬜ Planeado
```

End Stage Assessments em `performance/gate-reports/`.

---

## Literatura de referência

| Área | Obras principais |
|---|---|
| Referência normativa | PMBOK 8th Ed. (EN), PMBOK 7th Ed. (PT) |
| Software | Software Extension to PMBOK Guide 5th Ed. |
| Portfólio | Standard for Portfolio Management 4th Ed. |
| OPM | OPM Standard Vol. 1 + Vol. 2 |
| PMO operacional | PMO Practice Guide (PT) |
| Medição | EVM Standard |
| Cronograma | Scheduling Practice Standard 3rd Ed. |
| Mudança | Managing Change in Organizations |
| Estratégia | Wardley Maps |
| Transformação | Leading AI Transformation |

Biblioteca completa em `/home/RID/ring/pmo-team/skills/docs/` — ver `README.md` para índice por skill.

---

*Governance: PMI/PMBOK 8th Edition (2023) + PMO Practice Guide (PMI)*
*Processo: Ring dev-cycle | Actualização: cada End Stage Assessment*
