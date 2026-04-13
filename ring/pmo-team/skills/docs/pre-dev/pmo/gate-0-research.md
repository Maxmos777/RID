---
feature: framework-thinking-agent-model
gate: 0
date: 2026-04-10
research_mode: greenfield
agents_dispatched: 4
topology:
  scope: fullstack
  structure: monorepo
  reference_repo:
    path: ring/pmo-team/
    role: Plugin Ring PMO existente (skills, agentes, biblioteca `skills/docs/`)
  target_repo:
    path: ring/pmo-team/skills/framework-*/
    role: Skills propostas `ring:framework-*` e orquestrador compositional
  api_pattern: rpc
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
knowledge_base: ring/pmo-team/skills/docs/
appendix_wbs: ring/pmo-team/skills/docs/pre-dev/pmo/appendix-wbs-franquia.md
---

# Pesquisa Gate 0 — Framework Thinking Agent Model

## Resumo executivo

Consultorias em contextos de alta complexidade (franquia, expansão, transformação) carecem de um método replicável que una escuta do cliente, desenho estratégico e desdobramento até entregas e SLAs contratuais, sem perder alinhamento com a estratégia organizacional. A pesquisa conclui que a solução deve ser uma **camada compositional** sobre o ecossistema já existente no `ring-pmo-team` (p.ex. `ring:portfolio-planning`, agentes de risco e portfólio), ancorada no **OPM** (gestão de projetos organizacionais) e no **PMBOK** para o detalhe de domínios e ciclos. O desenho aprovado está consolidado no [design doc](../../../../docs/plans/2026-04-09-framework-thinking-agent-model-design.md); o presente documento formaliza evidências, lacunas e ligação normativa.

---

## Alinhamento estratégico (OPM)

O *Standard for Organizational Project Management* (PMI, 2018), edição em português em [`standards/project-management/opm-standard-volume-1.pdf`](../../standards/project-management/opm-standard-volume-1.pdf), trata a **estratégia organizacional** como base para implementar OPM: compreender para onde a organização (ou o cliente) pretende ir e **alinhar** portfólio, programas e projetos a essa direção, com adaptação ao contexto (princípios na secção 1.3.1, p.ex. alinhamento estratégico, valor, consistência na execução, integração com facilitadores organizacionais).

| Conceito OPM (resumo próprio) | Onde no standard (referência) | Implicação no Ring (actos / componentes) |
|-------------------------------|-------------------------------|----------------------------------------|
| Estratégia = plano de alto nível e processo de direção futura; operações e revisão de portfólio concretizam valor | Texto introdutório e fluxo em torno da Figura 1-1; definições de estratégia / operações / decisões de portfólio (Cap. 1) | **Acto 1** (`ring:framework-client-discovery`): captar visão, objectivos e restrições do cliente como “estratégia” do engagement |
| Relações portfólio ↔ programa ↔ projeto, todas ligadas ao plano estratégico | Secção **1.5**; Figuras **1-2** e **1-3** (estrutura e interacções) | **Acto 2** (`ring:framework-blueprint-analyzer`): gaps e contradições entre visão e prática; **Acto 3** (`ring:framework-pmbok-architect` + `ring:portfolio-planning`): hierarquia de iniciativas |
| “Compreender a estratégia organizacional” como passo inicial do OPM; PMO/EPMO alinham trabalho à estratégia | Secção **1.6** (Estratégia organizacional; maturidade 1.6.1; PMO/OPM 1.6.2; EPMO 1.6.3) | Orquestrador + integração com skills PMO existentes = função análoga a **governança e alinhamento** sem duplicar o PMO corporativo do cliente |
| Elementos críticos da **estrutura OPM** (metodologia, conhecimento, talentos, governança) | **Figura 3-1** *Elementos Críticos da Estrutura OPM* (p. impressa ~20 nesta edição; o índice pode referir outra numeração de figura conforme edição) | Checklist para **Standards Loading** e para validar cada skill `ring:framework-*` (metodologia + repositório de conhecimento em `skills/docs/`) |

*Nota de direitos autorais:* citações são resumos; o texto completo permanece no PDF da PMI.

---

## Modo de pesquisa

**greenfield** — O conjunto de skills `ring:framework-*` e o orquestrador são novos dentro do `ring-pmo-team`, embora reutilizem agentes e skills de portfólio/risco já existentes. A pesquisa combinou normas PMI, mapa de competências Ring e um case detalhado de franquia (preservado em anexo).

---

## Pesquisa no código (Repo Research Analyst)

### ring-pmo-team (referência) — padrões a replicar

| Tema | Referência |
|------|------------|
| Índice da biblioteca PDF por skill | [`ring/pmo-team/skills/docs/README.md`](../../README.md) — tabelas `using-pmo-team`, `portfolio-planning`, etc. |
| Skills PMO existentes | `ring/pmo-team/skills/using-pmo-team/SKILL.md`, skills de planeamento de portfólio, risco, reporting |
| Decisão compositional e gaps | [`gate-0-brainstorm.md`](gate-0-brainstorm.md) |

### Alvo — estado actual

| Tema | Referência |
|------|------------|
| Skills propostas (nomes e actos) | [design doc — diagrama e tabela de tasks](../../../../docs/plans/2026-04-09-framework-thinking-agent-model-design.md) |
| Mapeamento PDF → skill | Mesmo design doc, secção *Standards Loading*; alinhado a [`gate-6-dependency-map.md`](gate-6-dependency-map.md) |
| Case WBS franquia (árvore completa) | [`appendix-wbs-franquia.md`](appendix-wbs-franquia.md) |

### Lacuna principal (alvo vs referência)

- Falta implementação das skills `ring:framework-client-discovery`, `ring:framework-blueprint-analyzer`, `ring:framework-pmbok-architect`, `ring:framework-sla-generator` e `ring:framework-thinking-agent` com secções *Standards Loading* reais.
- O case de franquia estava embutido no rascunho comentado do Gate 0; foi **extraído para anexo** para o Gate 0 cumprir o template e permanecer legível para PRD/TRD.
- Alguns PDFs citados no design (p.ex. `opm-organizational-project-management-standard.pdf`) podem não existir no repositório; o análogo utilizável aqui é **`opm-standard-volume-1.pdf`** — ver secção *Documentação de frameworks* e [README harmonizado](../../README.md).

---

## Boas práticas externas (Best Practices Researcher)

| Tema | Fonte |
|------|--------|
| OPM — alinhamento estratégia / portfólio / programa / projeto | `ring/pmo-team/skills/docs/standards/project-management/opm-standard-volume-1.pdf` |
| Gestão de portfólio | `ring/pmo-team/skills/docs/standards/portfolio-strategy/portfolio-management-standard-4th.pdf` *(quando presente no clone)* |
| PMBOK / desempenho de projecto | `ring/pmo-team/skills/docs/standards/project-management/pmbok-guide-8th-eng.pdf` ou `pmbok-guide-7th-por.pdf` *(conforme existência)* |
| PMO operacional | `ring/pmo-team/skills/docs/practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` |
| Mapeamento estratégico | `ring/pmo-team/skills/docs/strategy-mapping/wardley-maps-simon-wardley.pdf` |
| Análise de negócio | `ring/pmo-team/skills/docs/business-analysis/pmi-guide-to-business-analysis.pdf` |
| Transformação / IA | `ring/pmo-team/skills/docs/transformation/leading-ai-transformation.pdf` |

---

## Documentação de frameworks (Framework Docs Researcher)

Espelho do *Standards Loading* do design doc, com **caminho canónico OPM** deste repositório:

| Skill proposta | PDF primário | PDF secundário |
|----------------|--------------|----------------|
| `ring:framework-client-discovery` | `standards/project-management/pmbok-guide-8th-eng.pdf` | `business-analysis/ba-practitioners-guide-2nd.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-blueprint-analyzer` | `standards/project-management/opm-standard-volume-1.pdf` | `strategy-mapping/wardley-maps-simon-wardley.pdf`, `standards/portfolio-strategy/portfolio-management-standard-4th.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-pmbok-architect` | `standards/project-management/pmbok-guide-8th-eng.pdf`, `standards/project-management/opm-standard-volume-1.pdf` | `standards/project-management/process-groups-practice-guide-eng.pdf`, `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` |
| `ring:framework-sla-generator` | `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` | `standards/portfolio-strategy/portfolio-management-standard-4th.pdf`, contrato de referência do engagement |
| `ring:framework-thinking-agent` | `standards/project-management/opm-standard-volume-1.pdf` | `transformation/leading-ai-transformation.pdf` |
| OPM via skills existentes | Ver [`README.md`](../../README.md) — `using-pmo-team`, `portfolio-planning`, `risk-management` | — |

---

## Pesquisa de produto / UX (Product Designer, modo ux-research)

- **Problema:** Consultores precisam de método estruturado, repetível e suportado por IA para escuta, síntese estratégica, desdobramento PMBOK/OPM e acordo de SLA, sem perder coerência com a estratégia do cliente.
- **Personas:** (1) **Consultor / PMO do franqueador** — entregar diagnóstico, blueprint e pacote operativo/jurídico com rastreabilidade; (2) **Patrocinador / fundador** — claridade de decisões, prioridades e riscos alinhados à expansão.
- **Padrão de mercado:** Pacotes de consultoria em franquia com manuais, cronogramas, contratos e governança; OPM e PMBOK como linguagem comum com enterprise.
- **Restrições de desenho:** Não substituir o PMO do cliente; reutilizar skills Ring; artefactos versionados em git; PDFs como âncora teórica legível por agentes.
- **Métricas sugeridas:** Tempo até blueprint aprovado; cobertura da árvore por domínios PMBOK; aderência do SLA a catálogo PMO; redução de retrabalho entre actos.

---

## Síntese (para PRD/TRD)

### Padrões a seguir (Ring + indústria)

1. Hierarquia **estratégia → portfólio → programa → projeto** explícita (OPM), com tailoring por segmento (case franquia no [anexo](appendix-wbs-franquia.md)).
2. **PMBOK 8** — princípios, domínios de desempenho e focus areas como espinha de controlo nos entregáveis (ver secções resumidas no anexo).
3. **Compositional architecture** — orquestrador invoca skills novas e delega OPM operacional a `ring:portfolio-planning` / agentes existentes ([brainstorm](gate-0-brainstorm.md)).
4. **Biblioteca `skills/docs/`** como fonte única de normas; cada skill nova declara *Standards Loading*.

### Restrições identificadas

- **PMI / copyright:** Resumir normas; não reproduzir figuras ou capítulos extensos nos repositórios públicos.
- **Ficheiros PDF ausentes:** Se `portfolio-management-standard-4th.pdf` ou outros não estiverem no clone, o agente deve degradar para paths indicados no README ou reportar bloqueio.
- **Escopo do Gate 0:** A árvore completa de processos não pertence ao corpo do research; mantém-se no [appendix-wbs-franquia.md](appendix-wbs-franquia.md).

### Perguntas abertas (para PRD)

1. Quais segmentos além de franquia alimentar entram na v1 do template library (T-002)?
2. O contrato tipo (`Contrato.pdf`) será sempre obrigatório para T-000/T-006 em engagements reais?
3. Onde publicar os JSON/YAML gerados (T-000–T-007) — só repositório do cliente ou também pacote Ring?

---

**Agentes utilizados (ring-pm-team / Gate 0):** `ring:repo-research-analyst`, `ring:best-practices-researcher`, `ring:framework-docs-researcher`, `ring:product-designer` (modo ux-research) — *planeado / consolidado nesta revisão documental*.

**Nota multi-repo:** N/A (monorepo Ring; consumo no repositório RID usa o mesmo caminho vendored `ring/pmo-team/`.)
