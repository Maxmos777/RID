---
feature: framework-thinking-agent-model
gate: 6
date: 2026-04-09
status: draft
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
trd_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-3-trd.md
topology:
  scope: methodology
  structure: single-repo
  plugin: ring/pmo-team
---

# Dependency Map — Framework Thinking Agent Model

## Seleção de tecnologias

**Princípio:** A v1 usa as ferramentas já presentes no ecossistema ring/RID. Zero novas dependências externas.

---

## Dependências de runtime

### 1. Ring Framework (pmo-team plugin)

| Dependência | Versão | Uso | Justificativa |
|-------------|--------|-----|---------------|
| ring pmo-team | vendored em `/home/RID/ring` | Skill de orquestração + agentes | Ecossistema nativo — sem nova dependência |
| ring default | vendored em `/home/RID/ring` | Hooks de sessão, patterns base | Base de todos os plugins ring |
| Claude Code (claude-sonnet-4-6) | atual | Executor dos agentes ring | Runtime de IA já disponível |

**Skills pmo-team existentes reutilizadas (arquitetura compositional):**

| Skill existente | Path | Uso no framework | Modo de operação |
|-----------------|------|-----------------|-----------------|
| `ring:portfolio-planning` | `ring/pmo-team/skills/portfolio-planning/SKILL.md` | Monitoramento OPM de alinhamento estratégico por domínio | Engagement mode — scope restrito ao `pmbok-tree.json` do engagement |
| `ring:portfolio-manager` | `ring/pmo-team/agents/portfolio-manager.md` | Agent delegado pelo portfolio-planning | Engagement mode — via `opm-config.yaml` |
| `ring:risk-analyst` | `ring/pmo-team/agents/risk-analyst.md` | RAID log do engagement | Engagement mode — via `risk-config.yaml` |

**Nota:** Estas skills NÃO são re-implementadas. O `ring:framework-opm-adapter` (T-007) produz ficheiros de configuração (`opm-config.yaml`, `risk-config.yaml`) que contextualizam as skills existentes para o engagement específico.

**Alternativas avaliadas:**
- LangChain como orquestrador: rejeitado — cria dependência externa e complexity sem ganho vs ring nativo.
- AutoGen: rejeitado — não se integra com ring pmo-team sem reescrever a skill layer.
- OPM Manager standalone (T-007 original): rejeitado — duplicaria lógica já presente em `ring:portfolio-planning` + `ring:risk-analyst`.

---

### 2. Armazenamento de Artefatos

| Dependência | Versão | Uso | Justificativa |
|-------------|--------|-----|---------------|
| Git | sistema | Versionamento de todos os artefatos | Já presente; imutabilidade por commit; sem nova infra |
| Sistema de ficheiros local | — | Armazenamento de engagements e templates | Simplicidade total na v1; migração para object storage em fase 2 se necessário |

**Alternativas avaliadas:**
- PostgreSQL para árvore PMBOK: rejeitado na v1 — overhead de schema, migrations e docker para problema que o filesystem resolve bem.
- S3/Object Storage: fase 2 — não necessário até múltiplos consultores concorrentes.

---

### 3. Formato de Dados

| Formato | Uso | Versão/Spec |
|---------|-----|-------------|
| JSON | `pmbok-tree.json`, `engagement-context.json`, `opm-indicators.json`, `contradicoes.yaml` | JSON Schema draft-07 para validação |
| YAML | `mapa-dimensional.yaml`, templates (`template.yaml`, `perguntas-escuta.yaml`) | YAML 1.2 |
| Markdown | Todos os artefatos legíveis por humanos (blueprint, SLA, relatórios OPM) | CommonMark 0.30 |

**Decisão YAML vs JSON para mapa-dimensional:** YAML para legibilidade do consultor durante sessão de escuta; JSON para processamento automático nos outros artefatos.

---

### 4. Motor de Análise de Contradições (F-002)

**Decisão v1: regras explícitas + assistência LLM contextual (sem LLM vendor dedicado)**

| Abordagem | Implementação | Justificativa |
|-----------|--------------|---------------|
| Regras de matching por dimensão | Lógica no agente `ring:framework-blueprint-analyzer` | Determinística, auditável, sem custo de API adicional |
| Análise semântica de contradições | Claude (via ring skill) usando o mapa dimensional como contexto | Já disponível no runtime — sem nova dependência |
| Melhores práticas do segmento | Ficheiro Markdown `melhores-praticas.md` no template | Editável pelo consultor; versionado via git |

**Alternativas avaliadas:**
- RAG com vector DB: rejeitado na v1 — over-engineering para volume de dados atual (poucos templates, poucos engagements).
- Fine-tuning de modelo específico para contradições PMO: rejeitado — custo e complexidade não justificados na v1.

---

### 5. Geração de SLA (F-006)

| Dependência | Uso | Versão |
|-------------|-----|--------|
| Markdown (CommonMark) | Formato do SLA | 0.30 |
| Python-markdown / pandoc | Conversão para PDF (fase 2) | Fase 2 — não no MVP |

**Decisão v1:** SLA em Markdown puro. PDF é fase 2 (quando cliente solicitar documento formal para assinatura digital).

---

### 6. Schema Validation

| Dependência | Uso | Versão |
|-------------|-----|--------|
| `jsonschema` (Python) | Validação do `pmbok-tree.json` contra schema definido no TRD | `jsonschema>=4.17` |

**Alternativa avaliada:** Pydantic para schema PMBOK Tree — preferível para implementação Python futura, mas ring é markdown-first; jsonschema é suficiente para v1.

---

### 7. Biblioteca PDF como Âncora Teórica (Standards Loading)

**Princípio:** Zero dependências externas de conteúdo — toda a fundamentação teórica está na biblioteca PDF local (`ring/pmo-team/skills/docs/`). Cada skill carrega os seus PDFs primários antes de executar.

| Skill | PDFs primários | PDFs secundários |
|-------|---------------|-----------------|
| `ring:framework-client-discovery` | `standards/project-management/pmbok-guide-8th-eng.pdf` | `business-analysis/ba-practitioners-guide-2nd.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-blueprint-analyzer` | `standards/project-management/opm-standard-volume-1.pdf` | `strategy-mapping/wardley-maps-simon-wardley.pdf`, `standards/portfolio-strategy/portfolio-management-standard-4th.pdf`, `business-analysis/pmi-guide-to-business-analysis.pdf` |
| `ring:framework-pmbok-architect` | `standards/project-management/pmbok-guide-8th-eng.pdf`, `standards/project-management/opm-standard-volume-1.pdf` | `standards/project-management/process-groups-practice-guide-eng.pdf`, `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` |
| `ring:framework-sla-generator` | `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` | `standards/portfolio-strategy/portfolio-management-standard-4th.pdf`, `docs/Contrato de Prestação de Serviços de Consultoria em Franquia.pdf` |
| `ring:framework-thinking-agent` | `standards/project-management/opm-standard-volume-1.pdf` | `transformation/leading-ai-transformation.pdf` |
| Skills existentes (`ring:portfolio-planning`, `ring:risk-analyst`) | Já mapeado em `pmo-team/skills/using-pmo-team/SKILL.md` | — |

**Protocolo de carregamento por skill:**
1. Carregar PDFs primários como contexto teórico via Read (path relativo a `ring/pmo-team/skills/docs/`)
2. Citar secção/capítulo relevante nos artefatos gerados (rastreabilidade metodológica)
3. Contradições entre o mapa dimensional do cliente e os PDFs → sinais de gap estratégico documentados no blueprint

---

## Dependências de desenvolvimento

| Dependência | Versão | Uso |
|-------------|--------|-----|
| Python | `>=3.12` | Scripts de validação de schema e geração de relatórios OPM |
| uv | atual | Gestão de dependências Python (consistente com backend RID) |
| pytest | `>=9.0` | Testes de validação de schema e de geração de artefatos |

---

## Estrutura de ficheiros final

```
ring/pmo-team/skills/
├── framework-thinking-agent/
│   └── SKILL.md                          ← skill de orquestração (ring:framework-thinking-agent)
├── framework-client-discovery/
│   └── SKILL.md                          ← agente Acto 1
├── framework-blueprint-analyzer/
│   └── SKILL.md                          ← agente Acto 2
├── framework-pmbok-architect/
│   └── SKILL.md                          ← agente Acto 3 (estrutura)
├── framework-opm-manager/
│   └── SKILL.md                          ← agente OPM (monitoramento)
├── framework-sla-generator/
│   └── SKILL.md                          ← gerador de SLA
├── shared-patterns/
│   ├── pmbok-tree-schema.json            ← JSON Schema do contrato de dados
│   └── engagement-context-schema.json    ← schema de contexto de engagement
└── docs/
    ├── templates/
    │   └── franchise/
    │       ├── template.yaml
    │       ├── perguntas-escuta.yaml
    │       ├── melhores-praticas.md
    │       └── CHANGELOG.md
    ├── engagements/                       ← criado por engagement, não commitado (gitignored)
    │   └── {client-slug}/
    │       └── ...
    └── pre-dev/
        └── pmo/
            └── (este conjunto de artefatos)
```

**Nota sobre engagements:** O diretório `docs/engagements/` é gitignored por defeito — dados de clientes não são commitados no repositório ring. Cada consultor mantém os seus engagements localmente ou num repositório privado do cliente.

---

## Riscos de dependência

| Dependência | Risco | Mitigação |
|-------------|-------|-----------|
| Claude (runtime) | Qualidade de análise de contradições depende do LLM | Regras explícitas como safety net; validação humana obrigatória antes de aprovar blueprint |
| Sistema de ficheiros local | Sem concorrência — dois consultores no mesmo engagement podem ter conflitos | v1 é single-user; fase 2 avalia git branching ou locking |
| YAML manual nos templates | Templates incorretos quebram o fluxo de pré-população | JSON Schema validation nos templates antes de usar em engagement |

---

## Gate 6 validation

| Categoria | Requisito | Estado |
|-----------|-----------|--------|
| Todas as tecnologias selecionadas com justificativa | Ring, git, JSON/YAML/Markdown, Python | ✅ |
| Versões fixadas (sem "latest") | jsonschema>=4.17, Python>=3.12, YAML 1.2, CommonMark 0.30 | ✅ |
| Alternativas avaliadas e rejeitadas documentadas | PostgreSQL, RAG, LangChain, Fine-tuning | ✅ |
| Stack coerente com ecossistema existente (ring/RID) | Zero novas dependências externas | ✅ |
| Riscos de dependência identificados | 3 riscos documentados com mitigação | ✅ |

**Resultado:** ✅ PASS → Gate 7 (Task Breakdown)
