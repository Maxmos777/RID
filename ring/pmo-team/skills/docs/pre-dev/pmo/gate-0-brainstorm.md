---
feature: framework-thinking-agent-model
gate: 0
type: brainstorm
date: 2026-04-09
status: approved
method: ring:brainstorming (Socratic method)
phases_completed: [Prep, Phase1, Phase2, Phase3, Phase4]
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
---

# Brainstorm — Framework Thinking Agent Model

## Decisão central

**Arquitectura Compositional** — o Framework é uma camada de orquestração sobre skills/agents PMO existentes. Não duplica funcionalidade.

## Gaps identificados no pre-dev (gates 1–7)

| Gap | Impacto | Resolução |
|-----|---------|-----------|
| T-007 duplicava `ring:portfolio-manager` + `ring:risk-analyst` | −5h desnecessárias; drift com ecossistema | T-007 → integration adapter (2h); delegar para skills existentes |
| `wbs-contrato-consultoria-franquia.html` tratado como input | Template derivado de artefato incompleto | Reposicionado como OUTPUT gerado pelo `ring:framework-pmbok-architect` |
| PDFs da biblioteca (`docs/`) não referenciados | Skills sem âncora teórica — risco de deriva metodológica | Mapeamento PDF → componente adicionado ao TRD e gate-6 |
| `pmbok-flow-franquia.html` ignorado | Template franchise derivado do zero | Reposicionado como input canônico para T-002 |
| `Contrato.pdf` ignorado | SLA Generator sem referência legal real | Adicionado como input formal do T-006 |
| T-000 ausente | T-002 sem extração estrutural dos artefatos visuais | T-000 adicionada: extração de `pmbok-flow-franquia.html` + Contrato.pdf |

## Posicionamento dos artefatos visuais

```
INPUTS (referências)                    OUTPUTS (gerados pelo framework)
─────────────────────                   ────────────────────────────────
pmbok-flow-franquia.html      ──┐
Contrato.pdf                  ──┼─→ T-000 (extração estrutural)
gate-0-research.md            ──┤
appendix-wbs-franquia.md      ──┘       │
                                        ▼
                                   template.yaml (T-002)
                                   sla-v1.md (T-006)
                                   mapa-dimensional.yaml (T-003)
                                   blueprint-estrategico.md (T-004)
                                   pmbok-tree.json (T-005)
                                   wbs-{engagement}.html  ← gerado + refinado
                                   [wbs-contrato-consultoria-franquia.html
                                    = 1ª instância incompleta; framework
                                      completa no 1º engagement franchise]
```

## Mapeamento teórico: PDF library → componentes

| Componente | PDFs de âncora teórica |
|-----------|----------------------|
| `ring:framework-client-discovery` | PMBOK 8 (Stakeholders Domain, Principles), BA Practitioners Guide, PMI Guide to BA |
| `ring:framework-blueprint-analyzer` | `standards/project-management/opm-standard-volume-1.pdf` (strategy→delivery), Wardley Maps, Portfolio Std 4th (strategic fit), PMI BA (gap analysis) |
| `ring:framework-pmbok-architect` | PMBOK 8 (7 Domains + 5 Focus Areas + Tailoring), `opm-standard-volume-1.pdf` (hierarchy), Process Groups Practice Guide, PMO Practice Guide |
| `ring:framework-sla-generator` | PMO Practice Guide (service catalog + SLA), Portfolio Std 4th (governance), Contrato.pdf (reference) |
| OPM via `ring:portfolio-planning` | Já mapeado no `using-pmo-team` README |
| OPM via `ring:risk-analyst` | Já mapeado no `using-pmo-team` README |
| `ring:framework-thinking-agent` | `opm-standard-volume-1.pdf` (framework geral), Leading AI Transformation |

## Arquitectura final aprovada

```
ring:framework-thinking-agent  [orquestrador]
  ├── ring:framework-client-discovery     [nova]
  ├── ring:framework-blueprint-analyzer   [nova]
  ├── ring:framework-pmbok-architect      [nova — gera wbs-{engagement}.html]
  ├── ring:portfolio-planning             [EXISTENTE — engagement mode]
  │     └── ring:portfolio-manager        [EXISTENTE — agent]
  │     └── ring:risk-analyst             [EXISTENTE — agent]
  └── ring:framework-sla-generator        [nova]
```

## Revisão de tasks

| Task | Antes | Depois |
|------|-------|--------|
| T-000 | — | Extração estrutural PDFs → schema (2h, nova) |
| T-002 | Estrutura inventada (4h) | Estrutura derivada de `pmbok-flow-franquia.html` + Contrato.pdf (4h) |
| T-005 | Árvore + JSON + MD (7h) | + geração `wbs-{engagement}.html` (7h — mesmo esforço, entregável adicional) |
| T-007 | OPM Manager standalone (5h) | Integration adapter para portfolio-planning + risk-analyst (2h) |
| **Total** | **37h** | **36h** |
