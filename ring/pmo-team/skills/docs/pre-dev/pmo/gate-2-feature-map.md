---
feature: framework-thinking-agent-model
gate: 2
date: 2026-04-09
status: draft
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
prd_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-1-prd.md
research_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-research.md
topology:
  scope: methodology
  structure: single-repo
  plugin: ring/pmo-team
---

# Feature Map — Framework Thinking Agent Model

## Overview

| Campo | Valor |
|-------|-------|
| PRD | `ring/pmo-team/skills/docs/pre-dev/pmo/gate-1-prd.md` (Gate 1) |
| Research | `ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-research.md` |
| Anexo (árvore case) | `ring/pmo-team/skills/docs/pre-dev/pmo/appendix-wbs-franquia.md` |
| Status | Draft — Gate 2 |
| Última actualização | 2026-04-10 |

---

## Feature inventory

### Core (Acto 1 + 2 — fundação do framework)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-001 | Protocolo de Escuta Estruturada | Guia o consultor por 6 dimensões de escuta (visão, objetivos, desafios, oportunidades, riscos, benefícios/custos), produzindo mapa dimensional auditável | Consultor não omite nenhuma dimensão crítica; artefato de escuta é rastreável | — | F-002, F-006 |
| F-002 | Motor de Blueprint Estratégico | Analisa o mapa dimensional vs melhores práticas do segmento; identifica alinhamentos e contradições; propõe estrutura de prioridades | Consultor chega à segunda reunião com evidência analítica, não opinião | F-001 | F-003, F-004 |
| F-003 | Construção da Árvore PMBOK | Cria e mantém a hierarquia Estratégia → Portfólio → Programa → Projeto → Flow → Processo, com domínios PMBOK, focus area e estado por nó | PMO Lead tem visibilidade total da hierarquia e rastreabilidade estratégica | F-002 | F-005, F-006 |

### Supporting (Acto 3 — execução e replicação)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-004 | Biblioteca de Templates por Segmento | Templates pré-definidos de Programa → Projeto → Flow → Processo por segmento de cliente; o case de franquia é o primeiro template | Consultor parte de estrutura validada; reduz tempo de configuração de novo engagement | F-002 | — |
| F-005 | OPM Flow Management | Monitoramento contínuo de alinhamento estratégico por domínio; alertas de desvio; integração de lessons learned | PMO Lead identifica desvios antes de virarem problemas; templates evoluem com lições aprendidas | F-003 | — |
| F-006 | SLA Contratual por Engagement | Gera documento de SLA a partir da árvore PMBOK do engagement: programas, entregáveis, critérios de aceite, preço/prazo | Cliente e consultor têm expectativas formalmente alinhadas desde o início | F-001, F-003 | — |

### Enhancement (Fase 2)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-007 | Dashboard de Portfólio (UI) | Interface visual para navegar na árvore PMBOK, ver indicadores de alinhamento e estado dos projetos | Adoção mais ampla por PMO Leads menos técnicos | F-003, F-005 | — |
| F-008 | Integração com ferramentas externas | Sincronização bidirecional com Jira, Asana ou Monday a partir da árvore PMBOK | Não obriga a abandonar ferramentas já em uso | F-003 | — |

---

## Domain groupings

### Domínio 1 — Discovery (Escuta e Diagnóstico)

**Propósito:** Capturar, de forma estruturada e replicável, a perspetiva do cliente sobre o seu negócio nas 6 dimensões críticas, produzindo o artefato de entrada para a análise estratégica.

**Features:** F-001 (Protocolo de Escuta), parte de F-006 (SLA — dimensão de escopo acordado)

**Owns:**
- Protocolo de perguntas estruturadas por dimensão (visão, objetivos, desafios, oportunidades, riscos, benefícios/custos)
- Mapa dimensional do cliente (artefato de saída do Acto 1)
- Registro de contexto do cliente (segmento, maturidade, SLA esperado)

**Provides para outros domínios:**
- Mapa dimensional → Domínio de Análise Estratégica (F-002)
- Contexto de engagement → Domínio de Governança/SLA (F-006)

**Consumes:**
- Template de perguntas do segmento (se existe template — da Biblioteca de Templates, F-004)

**Integration points:**
- ← Biblioteca de Templates: perguntas contextualizadas ao segmento
- → Domínio de Análise: mapa dimensional estruturado

---

### Domínio 2 — Análise Estratégica (Blueprint)

**Propósito:** Produzir, em bastidores e sem expor o processo ao cliente, um blueprint estratégico que explicita contradições entre visão e realidade e serve de fundação para os programas de trabalho.

**Features:** F-002 (Motor de Blueprint)

**Owns:**
- Processo de análise de contradições (visão do cliente × melhores práticas do segmento)
- Geração do blueprint estratégico versionado
- Mapeamento de cada contradição a programas da árvore PMBOK

**Provides para outros domínios:**
- Blueprint com prioridades estratégicas → Domínio de Arquitetura PMBOK (F-003)
- Evidência analítica → Domínio de Governança/SLA (F-006, justificativa dos programas propostos)

**Consumes:**
- Mapa dimensional do cliente (Domínio Discovery, F-001)
- Melhores práticas do segmento (Biblioteca de Templates, F-004)

**Integration points:**
- ← Domínio Discovery: mapa dimensional
- ← Biblioteca de Templates: padrões e benchmarks do segmento
- → Domínio Arquitetura PMBOK: blueprint com programas a criar

---

### Domínio 3 — Arquitetura PMBOK (Árvore de Trabalho)

**Propósito:** Construir e manter a hierarquia completa de gestão do engagement, garantindo rastreabilidade desde a Estratégia até ao Processo atómico, com aplicação dos 7 Domínios de Desempenho e 5 Focus Areas do PMBOK 8.

**Features:** F-003 (Construção da Árvore PMBOK)

**Owns:**
- Hierarquia Estratégia → Portfólio → Programa → Projeto → Flow → Processo
- Estado de cada nó (Focus Area: Iniciar/Planejar/Executar/Monitorar/Encerrar)
- Domínios PMBOK aplicáveis por nó (Governança, Escopo, Cronograma, Finanças, Stakeholders, Recursos, Risco)
- Tipologia de projetos (Sazonal S vs Contínuo C)

**Provides para outros domínios:**
- Hierarquia estruturada → Domínio de Execução OPM (F-005, para monitoramento)
- Programas/entregáveis → Domínio de Governança/SLA (F-006, para geração automática do SLA)

**Consumes:**
- Blueprint estratégico (Domínio Análise, F-002)
- Templates de programas (Biblioteca de Templates, F-004, para pré-popular a hierarquia)

**Integration points:**
- ← Domínio Análise: blueprint com programas a criar
- ← Biblioteca de Templates: estrutura pré-definida de Programa → Processo
- → Domínio Execução OPM: árvore para monitoramento
- → Domínio Governança/SLA: programas e entregáveis para o SLA

---

### Domínio 4 — Execução e Replicação (OPM + Templates)

**Propósito:** Garantir que a execução dos programas se mantém alinhada à estratégia definida e que o conhecimento gerado num engagement alimenta os próximos.

**Features:** F-004 (Biblioteca de Templates), F-005 (OPM Flow Management)

**Owns:**
- Templates de Programa → Processo por segmento (franchise como template de referência)
- Mecanismo de monitoramento de alinhamento estratégico (7 Domínios PMBOK × indicadores)
- Alertas de desvio estratégico por severidade (crítico, alerta, observação)
- Ciclo de melhoria contínua: lessons learned → atualização de templates

**Provides para outros domínios:**
- Templates → todos os domínios como fonte de estrutura reutilizável
- Indicadores de alinhamento → PMO Lead (relatórios)
- Templates atualizados → próximos engagements do mesmo segmento

**Consumes:**
- Árvore PMBOK do engagement (Domínio Arquitetura, F-003)
- Lessons learned dos projetos concluídos

**Integration points:**
- ← Domínio Arquitetura: árvore PMBOK para monitoramento
- ← Projetos concluídos: lessons learned
- → Todos os domínios: templates de referência atualizados

---

### Domínio 5 — Governança e SLA

**Propósito:** Formalizar o acordo entre consultor e cliente, garantindo que o escopo do engagement é explícito, os entregáveis são mensuráveis e as alterações são rastreadas.

**Features:** F-006 (SLA Contratual)

**Owns:**
- Geração do documento SLA a partir da árvore PMBOK
- Versionamento de SLAs (SLA base + aditivos por alteração de escopo)
- Mapeamento de programas → entregáveis → critérios de aceite → preço/prazo

**Provides:**
- SLA formal → Cliente e Consultor (referência de resolução de disputas)
- Histórico de alterações de escopo → auditoria do engagement

**Consumes:**
- Mapa dimensional do cliente (Domínio Discovery, F-001 — para escopo acordado)
- Árvore PMBOK do engagement (Domínio Arquitetura, F-003 — para programas/entregáveis)

**Integration points:**
- ← Domínio Discovery: contexto e escopo inicial
- ← Domínio Arquitetura: hierarquia de programas e projetos
- → Cliente e Consultor: SLA formal assinável

---

## User journeys

### Journey 1 — Consultor conduz primeiro engagement com novo cliente (Franchise)

**Utilizador:** Consultor Estratégico
**Goal:** Conduzir engagement de consultoria de franchising do início ao primeiro entregável

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Consultor inicia engagement com template "franchise" | F-004 | Execução/Replicação | Template pré-carregado com 5 programas tipo |
| 2. Conduz sessão de escuta com o cliente | F-001 | Discovery | Mapa dimensional das 6 dimensões preenchido |
| 3. Sistema analisa contradições em bastidores | F-002 | Análise Estratégica | Blueprint estratégico gerado com prioridades |
| 4. Consultor valida blueprint e ajusta programas | F-002, F-003 | Análise + Arquitetura | Árvore PMBOK criada com 5 programas ajustados |
| 5. SLA gerado automaticamente da árvore | F-006 | Governança/SLA | Documento SLA com programas, entregáveis, preços |
| 6. Consultor apresenta proposta ao cliente | F-006 | Governança/SLA | Cliente assina SLA |

**Resultado de sucesso:** Engagement formalizado com blueprint + árvore PMBOK + SLA em menos de 1 dia de trabalho.

---

### Journey 2 — PMO Lead monitora alinhamento estratégico em andamento

**Utilizador:** PMO Lead (interno ao cliente)
**Goal:** Verificar se os projetos em execução estão alinhados à estratégia definida

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. PMO Lead acede ao painel de alinhamento | F-005 | Execução/OPM | Visão dos 7 Domínios PMBOK com indicadores |
| 2. Identifica alerta no Domínio Financeiro | F-005 | Execução/OPM | Projeto de CAPEX com desvio de 23% em relação ao plano |
| 3. Navega até ao nó do projeto na árvore | F-003 | Arquitetura PMBOK | Contexto completo: flow afetado, processos impactados |
| 4. Aciona ciclo de revisão do projeto | F-003, F-005 | Arquitetura + OPM | Projeto movido para Focus Area "Monitorar e Controlar" |
| 5. Lessons learned registadas após resolução | F-004 | Execução/Replicação | Template de franchise atualizado com novo critério de alerta |

---

### Journey 3 — Segundo engagement do mesmo segmento (aproveitamento de template)

**Utilizador:** Consultor Estratégico
**Goal:** Iniciar engagement com segundo cliente de franquia com base no template evoluído

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Consultor seleciona template "franchise v2" (atualizado com lessons learned) | F-004 | Execução/Replicação | Template com melhorias do 1º engagement |
| 2. Conduz escuta — o protocolo já inclui perguntas específicas de franchising | F-001 | Discovery | Escuta 40% mais focada que no 1º engagement |
| 3. Blueprint inclui benchmarks do 1º engagement como referência | F-002 | Análise | Blueprint mais calibrado — menos contradições genéricas |
| 4. Árvore gerada em metade do tempo (base no template) | F-003 | Arquitetura | 5 programas pré-populados, só personalizações necessárias |

---

### Journey 4 — Cliente solicita alteração de escopo

**Utilizador:** Consultor + Cliente
**Goal:** Adicionar programa de Operacional ao engagement após assinatura do SLA original

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Cliente solicita inclusão do Programa Operacional | F-006 | Governança/SLA | SLA original não inclui este programa |
| 2. Consultor adiciona programa Operacional à árvore | F-003 | Arquitetura PMBOK | Árvore atualizada com novo programa |
| 3. Sistema gera SLA aditivo automaticamente | F-006 | Governança/SLA | Aditivo com novos entregáveis, critérios, preço/prazo |
| 4. Cliente assina aditivo | F-006 | Governança/SLA | Scope change formal registado; SLA original preservado |

---

## Feature interaction map

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DOMÍNIO: DISCOVERY                                 │
│                                                                        │
│  F-001 Protocolo de Escuta Estruturada                                │
│  (6 dimensões: visão, objetivos, desafios, oportunidades, riscos,     │
│   benefícios/custos → Mapa Dimensional do Cliente)                    │
└────────────────────────────┬─────────────────────────────────────────┘
                              │ Mapa Dimensional
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    DOMÍNIO: ANÁLISE ESTRATÉGICA                       │
│                                                                        │
│  F-002 Motor de Blueprint Estratégico                                 │
│  (contradições visão × realidade → Blueprint versionado               │
│   com prioridades estratégicas e programas propostos)                 │
│                  ▲                                                     │
│         Templates de segmento (F-004)                                 │
└────────────────────────────┬─────────────────────────────────────────┘
                              │ Blueprint + Programas
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    DOMÍNIO: ARQUITETURA PMBOK                         │
│                                                                        │
│  F-003 Construção da Árvore PMBOK                                     │
│  (Estratégia → Portfólio → Programa → Projeto → Flow → Processo)     │
│  com 7 Domínios + 5 Focus Areas por nó                               │
└──────────┬──────────────────────────────┬────────────────────────────┘
           │ Árvore para monitoramento    │ Programas/entregáveis para SLA
           ▼                              ▼
┌────────────────────────┐    ┌────────────────────────────────────────┐
│  DOMÍNIO: EXECUÇÃO/OPM │    │    DOMÍNIO: GOVERNANÇA/SLA             │
│                        │    │                                         │
│  F-004 Templates       │    │  F-006 SLA Contratual                  │
│  (biblioteca por segm.)│    │  (gerado da árvore PMBOK + escopo      │
│                        │    │   de discovery; versões + aditivos)    │
│  F-005 OPM Management  │    │                                         │
│  (alinhamento estratég.│    │  → Cliente + Consultor                 │
│   alertas + lessons    │    │                                         │
│   learned → templates) │    │                                         │
└────────────────────────┘    └────────────────────────────────────────┘
```

### Dependency matrix

| Feature | Depende de | Bloqueia | Opcional |
|---------|-----------|---------|---------|
| F-001 Protocolo de Escuta | Template de perguntas do segmento (F-004, se disponível) | F-002, F-006 | F-004 |
| F-002 Motor de Blueprint | F-001, referências do segmento (F-004) | F-003 | F-004 |
| F-003 Árvore PMBOK | F-002 | F-005, F-006 | F-004 |
| F-004 Biblioteca de Templates | — (independente; é pré-requisito dos outros quando disponível) | — | F-001, F-002, F-003 |
| F-005 OPM Management | F-003 | — | — |
| F-006 SLA Contratual | F-001, F-003 | — | — |
| F-007 Dashboard UI (fase 2) | F-003, F-005 | — | — |
| F-008 Integrações externas (fase 2) | F-003 | — | — |

---

## Integration points da metodologia

**Topology:** Methodology | **Pattern:** Agent orchestration (ring pmo-team)

### Dependências de runtime por feature

| Feature | Dependência de execução | Direção | Notas |
|---------|------------------------|---------|-------|
| F-001 Protocolo de Escuta | ring:framework-client-discovery agent | Execução guiada | Agente conduz sessão e estrutura saída |
| F-002 Motor de Blueprint | ring:framework-blueprint-analyzer agent + melhores práticas segmento | Leitura + processamento | Análise de contradições em bastidores |
| F-003 Árvore PMBOK | ring:framework-pmbok-architect agent + schema PMBOK tree | Construção + escrita | Schema tipado garante rastreabilidade |
| F-004 Templates | Sistema de ficheiros ring pmo-team (skills/docs/) | Leitura/escrita | Templates como ficheiros markdown versionados |
| F-005 OPM Management | ring:framework-opm-manager agent + indicadores por domínio | Leitura + alerta | Polling periódico ou trigger por evento |
| F-006 SLA Contratual | ring:framework-sla-generator + árvore PMBOK | Geração automática | SLA derivado da árvore; versões em git |

### Artefatos de saída por domínio

| Domínio | Artefato | Formato | Versioning |
|---------|----------|---------|------------|
| Discovery | Mapa Dimensional do Cliente | Markdown + YAML | Git |
| Análise Estratégica | Blueprint Estratégico | Markdown | Git (imutável após aprovação) |
| Arquitetura PMBOK | Árvore PMBOK | JSON estruturado + Markdown | Git |
| Execução/OPM | Indicadores de alinhamento | JSON + Markdown | Git |
| Templates | Templates por segmento | Markdown + YAML | Git (versionado por segmento) |
| Governança/SLA | SLA + Aditivos | Markdown (PDF-exportável) | Git |

---

## Phasing strategy

### Fase 1 — MVP (fundação do padrão)

**Goal:** Framework funcional para o segmento de franquia — do primeiro engagement ao SLA formal.

**Features:** F-001, F-002, F-003, F-004 (template franchise apenas), F-006

**Valor entregue:**
- Consultor: protocolo de escuta + blueprint + árvore PMBOK + SLA em menos de 1 dia.
- Cliente: proposta estruturada com entregáveis claros e SLA formal.

**Critérios de sucesso:**
- 1 engagement completo executado com o framework (end-to-end)
- Blueprint gerado com ≥ 3 contradições identificadas
- SLA gerado automaticamente da árvore PMBOK
- Template de franchise pré-populado cobrindo os 5 programas do case

**Trigger para Fase 2:** MVP validado com 2 engagements reais.

---

### Fase 2 — OPM + Replicação

**Goal:** Monitoramento contínuo e evolução dos templates.

**Features:** F-005, F-004 (templates adicionais além de franchise), F-007 (UI), F-008 (integrações)

---

## Scope boundaries

### Incluído

- Protocolo de escuta de 6 dimensões (F-001)
- Motor de análise de contradições e geração de blueprint (F-002)
- Construção da árvore PMBOK com 6 níveis hierárquicos (F-003)
- Template de franchise completo (5 programas do case de referência) (F-004)
- Geração automática de SLA da árvore PMBOK (F-006)
- Versionamento de todos os artefatos via git
- Suporte a projetos sazonais (S) e contínuos (C)

### Excluído

| Item excluído | Motivo |
|---------------|--------|
| Dashboard visual de portfólio | Fase 2 |
| Integração com Jira/Asana/Monday | Fase 2 |
| Templates além de franchise | Fase 2 — validar padrão no segmento de referência primeiro |
| Execução direta dos processos do cliente | Fora do escopo — o framework estrutura, não executa |
| Gestão financeira real dos projetos | Fora do escopo metodológico |
| Multi-idioma | Fase 2 — pt-BR apenas na v1 |

---

## Risk assessment

| Feature | Complexidade | Razão | Mitigação |
|---------|-------------|-------|-----------|
| F-002 Motor de Blueprint | Alta | Análise de contradições requer calibração semântica por segmento | Começar com regras explícitas (não LLM puro); validar com consultor humano nas primeiras execuções |
| F-003 Árvore PMBOK | Média | Schema de 6 níveis hierárquicos precisa ser suficientemente flexível sem perder rastreabilidade | Definir schema JSON tipado como contrato antes de implementar os agents |
| F-005 OPM Management | Média | Definição de "alinhamento estratégico" é subjetiva sem calibração com PMO real | Piloto com um PMO Lead real antes de automatizar indicadores |
| F-006 SLA | Baixa | Geração automática depende da qualidade da árvore PMBOK (F-003) | SLA gerado mas sempre revisado por consultor antes de envio ao cliente |

---

## Gate 2 validation

| Categoria | Requisito | Estado |
|-----------|-----------|--------|
| Completude de features | Todas as features do PRD (RF-001 a RF-006) mapeadas como F-001 a F-006 | ✅ |
| Categorização | Core/Supporting/Enhancement definidas | ✅ |
| Domínios | 5 domínios com fronteiras claras (Discovery, Análise, Arquitetura, Execução/OPM, Governança) | ✅ |
| Jornadas de utilizador | 4 jornadas documentadas (novo engagement, monitoramento OPM, 2º engagement, scope change) | ✅ |
| Pontos de integração | Todos identificados (agents ring + artefatos por domínio) | ✅ |
| Prioridade e faseamento | Fase 1 (MVP franchise) e Fase 2 definidas com critérios | ✅ |
| Sem detalhes técnicos | Sem frameworks, schemas de código ou protocolos específicos | ✅ |

**Resultado:** ✅ PASS → Gate 3 (TRD)
