# Design — Framework Thinking Agent Model

**Data:** 2026-04-09  
**Método:** ring:brainstorming (Socratic, 4 fases)  
**Status:** Aprovado — pronto para Gate 8 (Subtask Creation)  
**Pre-dev:** `ring/pmo-team/skills/docs/pre-dev/pmo/`

---

## Problema

Consultorias que operam em contextos de alta complexidade (franchising, expansão, transformação organizacional) não têm metodologia estruturada, replicável e amplificada por IA que unifique: escuta do cliente → blueprint estratégico → hierarquia PMBOK → SLA contratual → monitoramento de alinhamento.

---

## Decisão arquitectural: Compositional

O Framework não é um sistema standalone — é uma **camada de orquestração** sobre o ecossistema ring pmo-team existente. Skills e agentes já existentes (`ring:portfolio-planning`, `ring:portfolio-manager`, `ring:risk-analyst`) são reutilizados em "engagement mode" para o Acto 3 (OPM).

```
ring:framework-thinking-agent        ← orquestrador (skill principal)
  │
  ├─ Acto 1: ring:framework-client-discovery
  │          └─ âncora teórica: PMBOK 8 Stakeholders Domain
  │                             BA Practitioners Guide
  │                             PMI Guide to Business Analysis
  │
  ├─ Acto 2: ring:framework-blueprint-analyzer
  │          └─ âncora teórica: OPM Standard (strategy→delivery)
  │                             Wardley Maps (contradições)
  │                             Portfolio Std 4th (strategic fit)
  │                             PMI BA Guide (gap analysis)
  │
  ├─ Acto 3a: ring:framework-pmbok-architect
  │           └─ âncora teórica: PMBOK 8 (7 Domains + 5 Focus Areas + Tailoring)
  │                              OPM Standard (hierarquia 6 níveis)
  │                              Process Groups Practice Guide
  │                              PMO Practice Guide (PMO structure)
  │           └─ output adicional: wbs-{engagement}.html (gerado + refinado)
  │
  ├─ Acto 3b (OPM): ring:portfolio-planning  [EXISTENTE]
  │                  └─ ring:portfolio-manager agent
  │                  └─ ring:risk-analyst agent
  │                  └─ âncora teórica: já mapeada em using-pmo-team README
  │
  └─ Acto 3c: ring:framework-sla-generator
              └─ âncora teórica: PMO Practice Guide (service catalog + SLA)
                                 Portfolio Std 4th (governance)
                                 Contrato.pdf (referência legal real)
```

---

## Posicionamento dos artefatos visuais existentes

| Artefato | Papel | Localização |
|----------|-------|-------------|
| `pmbok-flow-franquia.html` | **Input canônico** — 5 programas × 5 Focus Areas para o template franchise | `docs/visual-references/` |
| `Contrato de Prestação de Serviços.pdf` | **Input legal** — estrutura de cláusulas para o SLA Generator | `docs/` |
| `wbs-contrato-consultoria-franquia.html` | **Output em construção** — gerado e refinado pelo `ring:framework-pmbok-architect` | `docs/visual-references/` |
| `wbs-contrato-consultoria-franquia.svg` | **Output derivado** — SVG exportado do HTML gerado | `docs/visual-references/` |

O `wbs-contrato-consultoria-franquia.html` existente é a **primeira instância incompleta** do output visual. O framework irá completá-lo quando o primeiro engagement franchise for executado com `ring:framework-pmbok-architect`.

---

## Biblioteca PDF como âncora teórica (Standards Loading)

Cada skill do framework tem uma secção "Standards Loading" que especifica quais PDFs da biblioteca `ring/pmo-team/skills/docs/` são carregados como contexto teórico antes de executar.

### Mapeamento completo

| Skill | PDFs primários | PDFs secundários |
|-------|---------------|-----------------|
| `ring:framework-client-discovery` | `standards/project-management/pmbok-guide-8th-eng.pdf` (Stakeholders Domain, Principles) | `business-analysis/ba-practitioners-guide-2nd.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-blueprint-analyzer` | `standards/project-management/opm-standard-volume-1.pdf` | `strategy-mapping/wardley-maps-simon-wardley.pdf`, `standards/portfolio-strategy/portfolio-management-standard-4th.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-pmbok-architect` | `standards/project-management/pmbok-guide-8th-eng.pdf`, `standards/project-management/opm-standard-volume-1.pdf` | `standards/project-management/process-groups-practice-guide-eng.pdf`, `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` |
| `ring:framework-sla-generator` | `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` | `standards/portfolio-strategy/portfolio-management-standard-4th.pdf` + `Contrato.pdf` (real) |
| `ring:framework-thinking-agent` | `standards/project-management/opm-standard-volume-1.pdf` | `transformation/leading-ai-transformation.pdf` |

### Princípio de carregamento

```
Para cada skill ring:framework-*:
  1. Carregar PDFs primários como contexto teórico (via Read ou referência de path)
  2. Citar seção/capítulo relevante nos artefatos gerados
  3. Contradições entre o mapa dimensional do cliente e os PDFs de referência
     são sinais de gap estratégico — documentar no blueprint (Acto 2)
```

---

## Fluxo de artefatos

```
T-000 (extração estrutural)
  inputs:  pmbok-flow-franquia.html
           Contrato.pdf
  outputs: extraction-map.yaml (estrutura 5 programas × processos)
           sla-clauses-reference.yaml (cláusulas do contrato)

T-002 (template franchise)
  inputs:  extraction-map.yaml (de T-000)
           appendix-wbs-franquia.md (árvore completa do case)
           gate-0-research.md (síntese Gate 0)
           PMBOK 8 (teórico)
  outputs: templates/franchise/template.yaml
           templates/franchise/perguntas-escuta.yaml
           templates/franchise/melhores-praticas.md

T-003 (discovery)
  inputs:  templates/franchise/perguntas-escuta.yaml (se franchise)
           BA Practitioners Guide (elicitation — teórico)
  outputs: mapa-dimensional.yaml
           mapa-dimensional.md

T-004 (blueprint)
  inputs:  mapa-dimensional.yaml
           templates/franchise/melhores-praticas.md
           OPM Standard + Wardley Maps (teórico)
  outputs: blueprint-estrategico.md
           contradicoes.yaml

T-005 (pmbok architect)
  inputs:  blueprint-estrategico.md + contradicoes.yaml
           templates/franchise/template.yaml
           PMBOK 8 + OPM Standard (teórico)
  outputs: pmbok-tree.json
           pmbok-tree.md (ASCII)
           wbs-{engagement}.html  ← gerado/refinado

T-006 (SLA generator)
  inputs:  pmbok-tree.json
           mapa-dimensional.yaml (escopo)
           sla-clauses-reference.yaml (de T-000)
           PMO Practice Guide (teórico)
  outputs: sla-v1.md

T-007 (integration adapter — OPM)
  inputs:  pmbok-tree.json
  configures: ring:portfolio-planning (engagement mode)
              ring:risk-analyst (engagement mode)
  outputs: opm-config.yaml (contexto para as skills existentes)

T-008 (orquestrador)
  inputs:  todas as skills anteriores
  outputs: ring:framework-thinking-agent SKILL.md
           engagement-context.json (schema)
```

---

## Tasks revisadas (pós-brainstorm)

| Task | Descrição | AI-hours | Δ |
|------|-----------|----------|---|
| **T-000** *(nova)* | Extração estrutural: `pmbok-flow-franquia.html` + `Contrato.pdf` → `extraction-map.yaml` + `sla-clauses-reference.yaml` | 2 | +2 |
| T-001 | JSON Schema PMBOK Tree + schemas de contexto | 3 | = |
| T-002 | Template franchise — derivado de T-000 + gate-0-research.md | 4 | = |
| T-003 | `ring:framework-client-discovery` + Standards Loading (PMBOK 8 + BA guides) | 5 | = |
| T-004 | `ring:framework-blueprint-analyzer` + Standards Loading (OPM + Wardley) | 6 | = |
| T-005 | `ring:framework-pmbok-architect` + geração `wbs-{engagement}.html` + Standards Loading | 7 | = |
| T-006 | `ring:framework-sla-generator` + Standards Loading (PMO Guide + Contrato.pdf) | 4 | = |
| **T-007** *(revisada)* | Integration adapter: configura `ring:portfolio-planning` + `ring:risk-analyst` em engagement mode | **2** | **−3** |
| T-008 | `ring:framework-thinking-agent` — orquestrador compositional | 3 | = |
| **TOTAL** | | **36** | **−1** |

---

## Critérios de sucesso do design

- [ ] Cada skill tem secção "Standards Loading" com PDFs primários e secundários referenciados
- [ ] `wbs-contrato-consultoria-franquia.html` é gerado/refinado por `ring:framework-pmbok-architect` no 1º engagement franchise
- [ ] T-007 configura skills existentes sem criar duplicação de lógica OPM
- [ ] Template franchise derivado de `pmbok-flow-franquia.html` (não inventado)
- [ ] SLA Generator usa `Contrato.pdf` como referência de cláusulas reais
- [ ] Zero novas dependências externas — 100% ring nativo + PDF library existente

---

## Próximos passos

1. **Gate 8** — Subtask creation: decompor T-000 a T-008 em subtasks de 2–5 min
2. **Gate 9** — Delivery planning: roadmap com datas e responsável
3. **Implementação** — ring:dev-cycle começando por T-000 → T-001 → T-002 (sem dependências)

---

*Gerado por: ring:brainstorming | Aprovado em: 2026-04-09*
