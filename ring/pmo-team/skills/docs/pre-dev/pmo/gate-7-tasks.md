---
feature: framework-thinking-agent-model
gate: 7
date: 2026-04-09
status: draft
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
dependency_map_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-6-dependency-map.md
trd_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-3-trd.md
topology:
  scope: methodology
  structure: single-repo
  plugin: ring/pmo-team
ai_estimate_total: 36
confidence_overall: High
amended: 2026-04-09
amendment_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-brainstorm.md
---

# Tasks — Framework Thinking Agent Model

## Estimativa AI-agent-hours

**Total estimado:** 36 AI-agent-hours  
**Metodologia:** ring:dev-cycle (TDD onde aplicável — schemas e validações; skill SKILL.md como "código" para os agentes)  
**Stack:** ring pmo-team (Markdown skills + JSON schemas + Python validation)

---

## T-000 — Extração Estrutural de Artefatos de Referência

**Feature:** F-003 (Arquitetura PMBOK) + F-006 (SLA) | **Domínio:** Foundation  
**AI-agent-hours:** 2 | **Confiança:** High (95%)  
**Tipo:** Foundation — bloqueia T-002 (template) e T-006 (SLA, parcialmente)

> **Nota pós-brainstorm (2026-04-09):** Task adicionada após brainstorm. T-002 não pode ser derivado do zero — precisa de extração estrutural de `pmbok-flow-franquia.html` e `Contrato.pdf` como inputs canônicos.

### Descrição

Extrair estrutura de dados dos artefatos de referência existentes (`pmbok-flow-franquia.html` e `Contrato de Prestação de Serviços.pdf`) e normalizar em schemas YAML reutilizáveis pelo resto do pipeline. Esta task garante que o template franchise e o SLA são derivados de evidências reais, não inventados.

### Entregáveis

- `ring/pmo-team/skills/docs/templates/franchise/extraction-map.yaml` — estrutura extraída de `pmbok-flow-franquia.html`: 5 programas × 5 Focus Areas × projetos existentes
- `ring/pmo-team/skills/docs/templates/franchise/sla-clauses-reference.yaml` — cláusulas extraídas do `Contrato.pdf`: estrutura de fases, condições de alteração, penalidades, critérios de aceite formais

### Critério de aceite

- `extraction-map.yaml` cobre os 5 programas do fluxo HTML com todos os projetos e flows identificáveis
- `sla-clauses-reference.yaml` captura ≥ 5 cláusulas tipo do contrato real (prazo, pagamento, alteração de escopo, entregáveis, rescisão)
- Ambos os ficheiros têm comentários inline indicando a origem (secção do HTML / página do PDF)
- Revisão humana do consultor antes de usar em T-002 (os artefatos são inputs canônicos — não devem ter erros de extração)

### Dependências de leitura

- `ring/pmo-team/skills/docs/visual-references/pmbok-flow-franquia.html` — input HTML com o fluxo PMBOK de franquia
- `ring/pmo-team/skills/docs/Contrato de Prestação de Serviços de Consultoria em Franquia.pdf` — contrato real de referência

---

## T-001 — JSON Schema da PMBOK Tree e Contrato de Dados

**Feature:** F-003 (Arquitetura PMBOK) | **Domínio:** Arquitetura PMBOK  
**AI-agent-hours:** 3 | **Confiança:** High (95%)  
**Tipo:** Foundation — bloqueia T-004, T-005, T-007

### Descrição

Definir e validar o JSON Schema completo para `pmbok-tree.json`, `engagement-context.json` e `mapa-dimensional.yaml`. Estes schemas são o contrato de dados de todo o framework — todos os agentes produzem e consomem dados nestes formatos.

### Entregáveis

- `ring/pmo-team/skills/shared-patterns/pmbok-tree-schema.json` — JSON Schema draft-07 completo (6 níveis hierárquicos, tipos S/C, 7 domínios PMBOK, 5 focus areas)
- `ring/pmo-team/skills/shared-patterns/engagement-context-schema.json` — Schema de contexto do engagement
- `ring/pmo-team/skills/shared-patterns/mapa-dimensional-schema.yaml` — Schema do mapa dimensional (6 dimensões obrigatórias)
- `tests/test_pmbok_schema.py` — Testes de validação dos schemas com exemplos válidos e inválidos

### Critério de aceite

- Schema valida um `pmbok-tree.json` com os 5 programas do case de franquia sem erros
- Schema rejeita árvore com hierarquia incompleta (ex.: Projeto sem Flow)
- Schema rejeita Focus Area com valor fora do enum (`Iniciar|Planejar|Executar|Monitorar|Encerrar`)
- Todos os testes passam (`pytest tests/test_pmbok_schema.py`)

### TDD approach

```python
# RED: test_schema_valida_arvore_franchise_completa → falha (schema não existe)
# GREEN: criar pmbok-tree-schema.json completo
# REFACTOR: garantir que schema é legível por humanos (titles, descriptions)
```

---

## T-002 — Template de Franchise (Segmento de Referência)

**Feature:** F-004 (Biblioteca de Templates) | **Domínio:** Execução/Replicação  
**AI-agent-hours:** 4 | **Confiança:** High (92%)  
**Tipo:** Foundation — bloqueia T-003 (parcialmente), T-006 (parcialmente)

### Descrição

Criar o template completo do segmento de franquia com base no case documentado em `appendix-wbs-franquia.md` (árvore histórica extraída do Gate 0) e na síntese em `gate-0-research.md`. Este é o primeiro template da biblioteca e servirá como padrão para todos os outros segmentos. Inclui: estrutura dos 5 programas, projetos (S/C), flows, processos, perguntas de escuta contextualizadas e melhores práticas do segmento.

### Entregáveis

- `ring/pmo-team/skills/docs/templates/franchise/template.yaml` — estrutura completa (5 programas × todos os projetos, flows, processos do case)
- `ring/pmo-team/skills/docs/templates/franchise/perguntas-escuta.yaml` — 6 dimensões × perguntas contextualizadas para franchise
- `ring/pmo-team/skills/docs/templates/franchise/melhores-praticas.md` — benchmarks e padrões de referência do segmento franchise
- `ring/pmo-team/skills/docs/templates/franchise/CHANGELOG.md` — versão 1.0 inicial
- `tests/test_franchise_template.py` — validação do template contra `pmbok-tree-schema.json`

### Critério de aceite

- `template.yaml` valida contra `pmbok-tree-schema.json` sem erros
- 5 programas cobertos: Financeiro, Governança, Comercial, Operacional, Jurídico
- Cada programa tem pelo menos 1 projeto sazonal (S) e 1 contínuo (C)
- Perguntas de escuta cobrem as 6 dimensões obrigatórias
- `melhores-praticas.md` inclui ≥ 3 benchmarks por programa

### Conteúdo de referência

Extraído de `appendix-wbs-franquia.md` (árvore Estratégia → Processo) e sintetizado em `gate-0-research.md` (PMBOK 8, OPM, lacunas).

---

## T-003 — Skill `ring:framework-client-discovery` (Acto 1)

**Feature:** F-001 (Protocolo de Escuta) | **Domínio:** Discovery  
**AI-agent-hours:** 5 | **Confiança:** High (88%)  
**Depende de:** T-001 (schema mapa-dimensional), T-002 (template perguntas — opcional mas recomendado)

### Descrição

Implementar a skill `ring:framework-client-discovery` que conduz o consultor pela sessão de escuta estruturada de 6 dimensões, produz o `mapa-dimensional.yaml` validado e prepara a entrada para o Acto 2.

### Entregáveis

- `ring/pmo-team/skills/framework-client-discovery/SKILL.md` — skill completa com:
  - Frontmatter YAML (name, description, trigger, sequence)
  - Protocolo de perguntas por dimensão (6 dimensões)
  - Lógica de aprofundamento (perguntas de segundo nível)
  - Validação de completude por dimensão
  - Geração do `mapa-dimensional.yaml` e `mapa-dimensional.md`
  - Anti-rationalization table obrigatória
  - Blocker criteria (dimensão obrigatória não respondida → não avança)
  - Pressure resistance table
- `tests/test_client_discovery.py` — testes de validação do output da skill

### Critério de aceite

- SKILL.md contém as 8 seções obrigatórias (Standards Loading, Blocker Criteria, Cannot Be Overridden, Severity Calibration, Pressure Resistance, Anti-Rationalization, When Not Needed, output format)
- Output `mapa-dimensional.yaml` valida contra `mapa-dimensional-schema.yaml`
- Skill não avança se alguma das 6 dimensões estiver vazia
- Se template de segmento existe: usa perguntas contextualizadas; se não: usa protocolo genérico
- Sessão de escuta não expõe análise de contradições ao cliente (respeitando o Acto 1 do framework)

---

## T-004 — Skill `ring:framework-blueprint-analyzer` (Acto 2)

**Feature:** F-002 (Motor de Blueprint) | **Domínio:** Análise Estratégica  
**AI-agent-hours:** 6 | **Confiança:** Medium (72%) — análise de contradições tem componente semântico com variância  
**Depende de:** T-001 (schema), T-002 (melhores-praticas.md), T-003 (output mapa-dimensional)

### Descrição

Implementar a skill `ring:framework-blueprint-analyzer` que analisa o mapa dimensional contra as melhores práticas do segmento, identifica contradições e alinhamentos, e produz o blueprint estratégico versionado com propostas de programas.

### Entregáveis

- `ring/pmo-team/skills/framework-blueprint-analyzer/SKILL.md` — skill completa com:
  - Lógica de análise por dimensão (matching mapa vs melhores-praticas)
  - Classificação de contradições (impacto Alto/Médio/Baixo, domínio PMBOK afetado)
  - Classificação de alinhamentos (pontos fortes do cliente)
  - Propostas de programas ordenadas por prioridade (P0/P1/P2)
  - Geração de `blueprint-estrategico.md` (formato legível, imutável após aprovação)
  - Geração de `contradicoes.yaml` (estruturado para consumo do T-005)
  - Validação humana obrigatória antes de produzir o blueprint final
  - Anti-rationalization table (especialmente: "a contradição pode parecer óbvia mas precisa ser documentada")
- `tests/test_blueprint_analyzer.py` — testes com mapa-dimensional de exemplo

### Critério de aceite

- ≥ 3 contradições identificadas no case de franchise (vs melhores-praticas.md de T-002)
- Cada contradição mapeia para ≥ 1 domínio PMBOK e ≥ 1 programa proposto
- Blueprint inclui seção de "pontos fortes" (alinhamentos) — não só críticas
- `contradicoes.yaml` valida contra schema definido em T-001
- Blueprint é marcado como imutável após aprovação humana (instrução explícita na skill)

---

## T-005 — Skill `ring:framework-pmbok-architect` (Acto 3 — Estrutura)

**Feature:** F-003 (Árvore PMBOK) | **Domínio:** Arquitetura PMBOK  
**AI-agent-hours:** 7 | **Confiança:** High (85%)  
**Depende de:** T-001 (schema), T-002 (template), T-004 (contradicoes.yaml)

### Descrição

Implementar a skill `ring:framework-pmbok-architect` que constrói a hierarquia PMBOK completa do engagement (6 níveis) a partir do blueprint e das contradições, pré-populando com o template do segmento quando disponível.

### Entregáveis

- `ring/pmo-team/skills/framework-pmbok-architect/SKILL.md` — skill completa com:
  - Algoritmo de construção da árvore (blueprint → programas → template → árvore completa)
  - Regras de tipagem de projetos (S sazonal vs C contínuo)
  - Aplicação dos 7 Domínios PMBOK por nó
  - Aplicação da Focus Area inicial por nó (padrão: Iniciar)
  - Geração de `pmbok-tree.json` (validado contra schema T-001)
  - Geração de `pmbok-tree.md` com diagrama ASCII da hierarquia
  - Validação de rastreabilidade bidirecional (Estratégia ↔ Processo)
  - Gate blocker: árvore sem rastreabilidade completa não é aprovada
- `tests/test_pmbok_architect.py` — teste com case de franchise completo

### Critério de aceite

- `pmbok-tree.json` gerado para o case de franchise valida contra schema T-001 sem erros
- Árvore inclui os 5 programas do template (Financeiro, Governança, Comercial, Operacional, Jurídico)
- Cada nó tem: nome, domínio_pmbok_principal, focus_area_atual, tipo (para Projetos)
- `pmbok-tree.md` inclui diagrama ASCII legível da hierarquia completa
- Rastreabilidade verificada: cada Processo tem caminho até à Estratégia

---

## T-006 — Skill `ring:framework-sla-generator`

**Feature:** F-006 (SLA Contratual) | **Domínio:** Governança/SLA  
**AI-agent-hours:** 4 | **Confiança:** High (90%)  
**Depende de:** T-001 (schema), T-003 (mapa-dimensional), T-005 (pmbok-tree.json)

### Descrição

Implementar a skill `ring:framework-sla-generator` que gera o documento SLA a partir da árvore PMBOK e do mapa dimensional do engagement, suportando versões base e aditivos de scope change.

### Entregáveis

- `ring/pmo-team/skills/framework-sla-generator/SKILL.md` — skill completa com:
  - Algoritmo de extração de entregáveis da árvore PMBOK (Processo → Entregável)
  - Agrupamento de entregáveis por Fase (Focus Area)
  - Template de SLA (estrutura padronizada conforme TRD)
  - Lógica de aditivos (scope change → `sla-aditivo-NNN.md` sem modificar original)
  - Instrução explícita: SLA imutável após aprovação pelo consultor
  - Anti-rationalization: "o consultor pode ajustar manualmente mas o SLA precisa do git commit"
- `tests/test_sla_generator.py` — teste com pmbok-tree do case franchise

### Critério de aceite

- SLA gerado cobre todos os programas da árvore PMBOK do engagement
- Cada programa → lista de entregáveis com critério de aceite mensurável
- Aditivo gerado não modifica `sla-v1.md` — cria `sla-aditivo-001.md`
- SLA contém seção "Fora do escopo (explícito)" com itens da exclusão do PRD
- Consultor pode preencher preço/prazo (campos com placeholder) antes de enviar ao cliente

---

## T-007 — Integration Adapter OPM: `ring:framework-opm-adapter`

**Feature:** F-005 (OPM Management) | **Domínio:** Execução/OPM  
**AI-agent-hours:** 2 | **Confiança:** High (88%)  
**Depende de:** T-001 (schema), T-005 (pmbok-tree.json)

> **Nota pós-brainstorm (2026-04-09):** Revisada de 5h (standalone `ring:framework-opm-manager`) para 2h (integration adapter). A lógica de OPM é delegada para `ring:portfolio-planning` + `ring:risk-analyst` existentes. Esta task apenas produz os ficheiros de configuração que contextualizam as skills existentes para o engagement específico.

### Descrição

Implementar o integration adapter `ring:framework-opm-adapter` que lê o `pmbok-tree.json` do engagement e produz ficheiros de configuração (`opm-config.yaml`, `risk-config.yaml`) para operar as skills existentes do pmo-team em "engagement mode" — escopo restrito ao engagement em vez do portfólio global.

### Entregáveis

- `ring/pmo-team/skills/framework-opm-adapter/SKILL.md` — adapter com:
  - Leitura do `pmbok-tree.json` do engagement
  - Geração de `opm-config.yaml` (scope = programas/projetos do engagement, SLA thresholds, domínios a monitorar)
  - Geração de `risk-config.yaml` (programas em scope, riscos pré-identificados no `contradicoes.yaml` do blueprint)
  - Invocação de `ring:portfolio-planning` passando `opm-config.yaml` — output: relatório de alinhamento estratégico
  - Invocação de `ring:risk-analyst` passando `risk-config.yaml` — output: RAID log do engagement
  - Protocolo de lessons learned ao encerrar projeto (proposta de atualização do template do segmento)
- `tests/test_opm_adapter.py` — testes de geração de `opm-config.yaml` e `risk-config.yaml` para o case de franchise

### Critério de aceite

- `opm-config.yaml` gerado para o case de franchise cobre os 5 programas do `pmbok-tree.json`
- `risk-config.yaml` importa riscos do `contradicoes.yaml` como riscos pré-identificados
- Adapter invoca `ring:portfolio-planning` e `ring:risk-analyst` sem duplicar lógica de OPM
- Skill inclui instrução de que monitoramento OPM não é autónomo — consultor confirma indicadores antes de reportar ao cliente
- Lessons learned capturadas ao encerrar projeto com proposta de atualização do template do segmento

---

## T-008 — Skill de Orquestração: `ring:framework-thinking-agent`

**Feature:** Todas | **Domínio:** Orquestração  
**AI-agent-hours:** 3 | **Confiança:** High (88%)  
**Depende de:** T-003, T-004, T-005, T-006 (todas as skills dos agentes)

### Descrição

Implementar a skill principal `ring:framework-thinking-agent` que orquestra o fluxo de 3 actos, invoca os agentes especializados em sequência e mantém o contexto do engagement.

### Entregáveis

- `ring/pmo-team/skills/framework-thinking-agent/SKILL.md` — skill de orquestração com:
  - Sequência de gates: Discovery → Blueprint → Arquitetura → SLA
  - Invocação explícita de cada skill especializada via `Skill tool`
  - Manutenção de `engagement-context.json` entre sessões
  - Gate blockers entre cada fase (aprovação humana obrigatória)
  - Anti-rationalization: "MUST NOT skip human approval gate"
  - Handling de segmento: deteta template disponível e pré-configura skills
  - Seção "when to use" e "when not to use"
  - User-invocable: true (acessível via `/ring:framework-thinking-agent`)

### Critério de aceite

- Skill invoca T-003 → T-004 → T-005 → T-006 em sequência correta
- Cada gate exige aprovação humana antes de avançar (instrução explícita)
- `engagement-context.json` preserva estado entre sessões (consultor pode retomar engagement)
- Skill deteta template de franchise e passa para as sub-skills
- Todos os artefatos salvos em `docs/engagements/{client-slug}/`

---

## Resumo de tasks e estimativas

| Task | Feature(s) | AI-agent-hours | Confiança | Bloqueia |
|------|-----------|----------------|-----------|---------|
| T-000 Extração Estrutural | F-003, F-006 | 2 | High 95% | T-002, T-006 (parcial) |
| T-001 JSON Schema | F-003 | 3 | High 95% | T-004, T-005, T-007 |
| T-002 Template Franchise | F-004 | 4 | High 92% | T-003 (parcial), T-006 (parcial) |
| T-003 Client Discovery | F-001 | 5 | High 88% | T-008 |
| T-004 Blueprint Analyzer | F-002 | 6 | Medium 72% | T-005, T-008 |
| T-005 PMBOK Architect | F-003 | 7 | High 85% | T-006, T-007, T-008 |
| T-006 SLA Generator | F-006 | 4 | High 90% | T-008 |
| T-007 OPM Adapter | F-005 | 2 | High 88% | T-008 |
| T-008 Orquestrador | Todas | 3 | High 88% | — |
| **TOTAL** | | **36** | **High geral** | |

### Sequência de implementação recomendada

```
T-000 (extração) ──► T-002 (template) ──┐
                                         │
T-001 (schema) ──────────────────────────┼──► T-003 (discovery) ──► T-004 (blueprint) ──► T-005 (architect)
                                         │                                                        │
                                         └──► (parcial para T-006)                ┌──────────────┼──────────────┐
                                                                                   ▼              ▼              ▼
                                                                              T-006 (SLA)  T-007 (adapter)  T-008 (orch)
```

**Paralelismo possível:**
- T-000 e T-001 podem iniciar em paralelo (sem dependência entre si)
- T-002 e T-003 podem ser iniciadas em paralelo após T-000 + T-001 (T-003 não precisa do template completo — usa protocolo genérico)
- T-006, T-007 e T-008 podem ser iniciadas em paralelo após T-005

---

## Estimativa de calendário

**Fórmula:** `(ai_estimate × 1.5 / 0.90) / 8 / 1 desenvolvedor`

| Task | AI-hours | Calendário (dias) |
|------|----------|------------------|
| T-000 | 2 | 0.4 |
| T-001 | 3 | 0.6 |
| T-002 | 4 | 0.8 |
| T-003 | 5 | 1.0 |
| T-004 | 6 | 1.3 |
| T-005 | 7 | 1.5 |
| T-006 | 4 | 0.8 |
| T-007 | 2 | 0.4 |
| T-008 | 3 | 0.6 |
| **TOTAL** | **36** | **~7.4 dias** |

Com paralelismo (T-000 ∥ T-001; T-002 ∥ T-003 após; T-006 ∥ T-007 ∥ T-008 após T-005): **~5.0 dias calendário com 1 desenvolvedor**.

---

## Gate 7 validation

| Categoria | Requisito | Estado |
|-----------|-----------|--------|
| Todas as features cobertas | F-001 a F-006 têm tasks associadas | ✅ |
| Nenhuma task > 16 AI-agent-hours | Máximo: T-005 = 7h | ✅ |
| Todas as tasks com estimativa e confiança | 9 tasks com confiança declarada | ✅ |
| Tasks Medium com revisão necessária | T-004 (72%) — validação com consultor real recomendada | ✅ |
| Dependências mapeadas | Sequência e paralelismo documentados (inclui T-000) | ✅ |
| Cada task entrega valor | Cada task produz artefato utilizável independentemente | ✅ |
| Critérios de aceite testáveis | Todos os critérios são mensuráveis e verificáveis | ✅ |
| Arquitetura compositional refletida | T-007 = integration adapter (2h), não OPM standalone | ✅ |
| Artefatos de referência como inputs | T-000 extrai `pmbok-flow-franquia.html` + `Contrato.pdf` antes de T-002 | ✅ |

**Resultado:** ✅ PASS → Gate 8 (Subtask Creation) e Gate 9 (Delivery Planning)
