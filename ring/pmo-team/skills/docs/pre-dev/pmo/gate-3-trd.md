---
feature: framework-thinking-agent-model
gate: 3
date: 2026-04-09
status: draft
amended: 2026-04-09
amendment_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-brainstorm.md
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
prd_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-1-prd.md
feature_map_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-2-feature-map.md
topology:
  scope: methodology
  structure: single-repo
  plugin: ring/pmo-team
  implementation_type: ring-skill-agent-set
  architecture: compositional
---

# TRD — Framework Thinking Agent Model

## Princípio arquitetural

O Framework Thinking Agent Model é implementado como um **conjunto de skills e agentes Ring** dentro do plugin `ring/pmo-team`. Cada domínio do Feature Map mapeia a um ou mais agentes especializados, orquestrados por uma skill principal (`ring:framework-thinking-agent`). Os artefatos de cada etapa são ficheiros Markdown/JSON versionados via git — o sistema de ficheiros é a fonte de verdade, não uma base de dados separada.

**Separação de responsabilidades:**
- **Skill de orquestração** (`ring:framework-thinking-agent`): sequência de gates, invocação dos agentes, validações de gate.
- **Agentes especializados novos** (Actos 1, 2, 3a, 3c): executam a lógica única do framework sem equivalente no pmo-team.
- **Skills existentes reutilizadas** (`ring:portfolio-planning`, `ring:portfolio-manager`, `ring:risk-analyst`): operadas em "engagement mode" para o Acto 3b (OPM) — sem duplicação de lógica.
- **Schema PMBOK Tree** (contrato de dados): garante rastreabilidade hierárquica e interoperabilidade entre agentes.
- **Biblioteca de Templates** (ficheiros YAML/Markdown): estruturas reutilizáveis por segmento.
- **Biblioteca PDF** (`ring/pmo-team/skills/docs/`): âncora teórica — cada skill carrega PDFs primários via Standards Loading antes de executar.

### Arquitectura compositional

```
ring:framework-thinking-agent        [orquestrador]
  ├── ring:framework-client-discovery     [nova — sem equivalente]
  ├── ring:framework-blueprint-analyzer   [nova — sem equivalente]
  ├── ring:framework-pmbok-architect      [nova — sem equivalente]
  ├── ring:portfolio-planning             [EXISTENTE — engagement mode]
  │     └── ring:portfolio-manager        [EXISTENTE — agent delegado]
  │     └── ring:risk-analyst             [EXISTENTE — agent delegado]
  └── ring:framework-sla-generator        [nova — sem equivalente]
```

---

## Arquitetura de componentes

### Componente 1 — Skill de Orquestração: `ring:framework-thinking-agent`

**Responsabilidade:** Orchestrar o fluxo de 3 actos (Escuta → Blueprint → Árvore PMBOK), invocar os agentes especializados em sequência, validar os critérios de gate entre cada fase e manter o contexto do engagement.

**Comportamento:**
- Lê o template do segmento (se disponível) para pré-configurar perguntas e estrutura.
- Invoca `ring:framework-client-discovery` (Acto 1).
- Após aprovação humana do mapa dimensional, invoca `ring:framework-blueprint-analyzer` (Acto 2).
- Após aprovação do blueprint, invoca `ring:framework-pmbok-architect` (Acto 3 — estrutura).
- Ao final, invoca `ring:framework-sla-generator` para gerar o SLA do engagement.
- Salva estado do engagement em `engagement-context.json` (continuidade entre sessões).

**Inputs:**
- Nome do cliente, segmento, template de referência (opcional)
- Aprovações humanas a cada gate

**Outputs:**
- `mapa-dimensional.md` (Acto 1)
- `blueprint-estrategico.md` (Acto 2)
- `pmbok-tree.json` + `pmbok-tree.md` (Acto 3)
- `sla-engagement.md` (gerado após Acto 3)
- `engagement-context.json` (estado persistente)

**Armazenamento:** `ring/pmo-team/skills/docs/engagements/{client-slug}/`

**Standards Loading (teórico):**
- `standards/project-management/opm-standard-volume-1.pdf` — quadro OPM de estratégia→entrega como referência para a sequência de actos
- `transformation/leading-ai-transformation.pdf` — princípios de orquestração de agentes IA em contextos de transformação organizacional

---

### Componente 2 — Agente de Discovery: `ring:framework-client-discovery`

**Responsabilidade:** Conduzir a sessão de escuta estruturada com o consultor, cobrindo as 6 dimensões obrigatórias, e produzir o mapa dimensional validado.

**Comportamento:**
- Para cada dimensão (visão, objetivos, desafios, oportunidades, riscos, benefícios/custos): apresenta pergunta-guia, aguarda resposta, valida completude, faz perguntas de aprofundamento se necessário.
- Se template de segmento existe: usa perguntas contextualizadas do template.
- Ao final: apresenta resumo dimensional para validação humana.
- Produz `mapa-dimensional.yaml` com estrutura padronizada.

**Protocolo de perguntas (6 dimensões):**

```yaml
dimensions:
  visao:
    pergunta_guia: "Como você descreve o negócio que quer construir?"
    aprofundamento: ["Qual o posicionamento de mercado?", "Qual o diferencial competitivo?"]
    validacao: "campo obrigatório — sem resposta, engagement não avança"
  objetivos:
    pergunta_guia: "Quais são os objetivos estratégicos para os próximos 12-24 meses?"
    aprofundamento: ["São mensuráveis?", "Têm prazo definido?"]
  desafios:
    pergunta_guia: "Quais são os principais desafios que impedem atingir esses objetivos?"
    aprofundamento: ["O desafio é interno ou externo?", "Já tentou resolver antes?"]
  oportunidades:
    pergunta_guia: "Que oportunidades de mercado você identifica que ainda não explorou?"
    aprofundamento: ["Por que ainda não foram capturadas?"]
  riscos:
    pergunta_guia: "Quais riscos podem comprometer a estratégia definida?"
    aprofundamento: ["Probabilidade alta ou baixa?", "Impacto no negócio?"]
  beneficios_custos:
    pergunta_guia: "Qual o benefício esperado e o investimento que faz sentido para esse projeto?"
    aprofundamento: ["ROI esperado em que prazo?", "Existe orçamento aprovado?"]
```

**Outputs:** `mapa-dimensional.yaml`, `mapa-dimensional.md` (relatório legível)

**Standards Loading (teórico):**
- `standards/project-management/pmbok-guide-8th-eng.pdf` — Domínio Partes Interessadas (elicitação e engajamento de stakeholders) + Princípios PMBOK (capítulo 1–2)
- `business-analysis/ba-practitioners-guide-2nd.pdf` — técnicas de elicitação estruturada (entrevistas, workshops, análise de necessidades)
- `business-analysis/pmi-guide-to-business-analysis.pdf` — framework de análise de negócio para discovery de requisitos estratégicos

---

### Componente 3 — Agente de Blueprint: `ring:framework-blueprint-analyzer`

**Responsabilidade:** Analisar o mapa dimensional vs as melhores práticas do segmento, identificar contradições e alinhamentos, e produzir o blueprint estratégico versionado.

**Comportamento:**
- Carrega o mapa dimensional do engagement atual.
- Carrega as melhores práticas do segmento (do template ou da base de conhecimento do pmo-team).
- Para cada dimensão do mapa: identifica alinhamentos e contradições com as práticas de referência.
- Propõe estrutura de prioridades estratégicas (P0/P1/P2 por urgência e impacto).
- Mapeia cada contradição a domínios PMBOK e programas recomendados.
- Gera o blueprint como documento versionado (imutável após aprovação).

**Lógica de análise de contradições:**

```
Para cada dimensão D do mapa:
  1. Comparar D.resposta com template.melhores_praticas[D]
  2. Se divergência significativa → registar contradição com:
     - dimensão afetada
     - gap identificado
     - impacto estimado (Alto/Médio/Baixo)
     - domínio PMBOK afetado
     - programas recomendados para endereçar o gap
  3. Se alinhamento → registar ponto forte (ativo estratégico)
```

**Outputs:** `blueprint-estrategico.md`, `contradicoes.yaml` (mapeamento estruturado para a árvore PMBOK)

**Standards Loading (teórico):**
- `standards/project-management/opm-standard-volume-1.pdf` — ponte estratégia→entrega como modelo de referência para o blueprint (hierarquia 6 níveis)
- `strategy-mapping/wardley-maps-simon-wardley.pdf` — mapeamento de contradições e evolução estratégica por posição no mapa
- `standards/portfolio-strategy/portfolio-management-standard-4th.pdf` — alinhamento estratégico de portfólio e critérios de priorização
- `business-analysis/pmi-guide-to-business-analysis.pdf` — análise de gap estratégico e propostas de intervenção

---

### Componente 4 — Agente de Arquitetura: `ring:framework-pmbok-architect`

**Responsabilidade:** Construir a hierarquia PMBOK completa do engagement, garantindo rastreabilidade de 6 níveis e aplicação correta dos 7 Domínios e 5 Focus Areas.

**Comportamento:**
- A partir do blueprint e das contradições mapeadas: cria os nós raiz (Estratégia, Portfólio).
- Para cada programa recomendado no blueprint: cria o nó de Programa com domínios PMBOK aplicáveis.
- Se template de segmento existe: pré-popula Projeto → Flow → Processo a partir do template; consultor valida e ajusta.
- Se sem template: gera estrutura mínima e sinaliza para preenchimento humano.
- Valida rastreabilidade bidirecional (Estratégia ↔ Processo) antes de finalizar.

**Schema PMBOK Tree (contrato de dados):**

```json
{
  "engagement_id": "string (slug único)",
  "created_at": "ISO8601",
  "version": "semver",
  "estrategia": {
    "nome": "string",
    "descricao": "string",
    "dominios_pmbok": ["Governança", "Escopo", "Partes interessadas", "Risco"],
    "portfolio": {
      "nome": "string",
      "programas": [
        {
          "nome": "string",
          "dominio_pmbok_principal": "string",
          "focus_area_atual": "Iniciar|Planejar|Executar|Monitorar|Encerrar",
          "projetos": [
            {
              "nome": "string",
              "tipo": "S|C",
              "flows": [
                {
                  "nome": "string",
                  "processos": [
                    {"nome": "string", "entregavel": "string", "criterio_aceite": "string"}
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

**Outputs:** `pmbok-tree.json` (schema tipado), `pmbok-tree.md` (representação legível com diagrama ASCII)

**Standards Loading (teórico):**
- `standards/project-management/pmbok-guide-8th-eng.pdf` — 7 Domínios de Desempenho + 5 Focus Areas + tailoring (capítulos 4–8)
- `standards/project-management/opm-standard-volume-1.pdf` — hierarquia OPM de 6 níveis (Estratégia → Portfólio → Programa → Projeto → Flow → Processo)
- `standards/project-management/process-groups-practice-guide-eng.pdf` — grupos de processo e entregáveis por domínio
- `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` — estrutura de PMO e critérios de tipologia de projetos

---

### Componente 5 — Integration Adapter OPM: `ring:framework-opm-adapter`

> **Nota pós-brainstorm (2026-04-09):** Componente originalmente planeado como `ring:framework-opm-manager` (skill autónoma) foi convertido para integration adapter após decisão de arquitectura compositional. A lógica de OPM é delegada para `ring:portfolio-planning` (skill existente) e `ring:risk-analyst` (agent existente) operados em "engagement mode". Não há duplicação de lógica.

**Responsabilidade:** Configurar as skills existentes do pmo-team para operar com o contexto do engagement específico (scope = programas do `pmbok-tree.json`), em vez de portfólio global.

**Comportamento:**
- Lê o `pmbok-tree.json` do engagement.
- Produz `opm-config.yaml`: contexto de engagement para `ring:portfolio-planning` (lista de projetos, SLA thresholds, domínios a monitorar).
- Produz `risk-config.yaml`: contexto de engagement para `ring:risk-analyst` (programas em scope, riscos pré-identificados do blueprint).
- Invoca `ring:portfolio-planning` passando `opm-config.yaml` como contexto — output: relatório de alinhamento estratégico por domínio.
- Invoca `ring:risk-analyst` passando `risk-config.yaml` — output: RAID log do engagement.
- Captura lessons learned ao encerrar projeto e propõe actualização do template do segmento.

**Standards Loading (teórico):**
- Skills existentes já têm os seus próprios PDFs mapeados em `using-pmo-team` README.
- Adapter consulta adicionalmente: `standards/project-management/opm-standard-volume-1.pdf` (cap. OPM Execution) para calibrar thresholds do `opm-config.yaml`.

**Outputs:** `opm-config.yaml`, `risk-config.yaml` (configuração das skills existentes), `lessons-learned.md` (por projeto encerrado)

---

### Componente 6 — Gerador de SLA: `ring:framework-sla-generator`

**Responsabilidade:** Gerar o documento SLA do engagement a partir da árvore PMBOK e do contexto de discovery, suportando versões base e aditivos.

**Comportamento:**
- Lê `pmbok-tree.json` e `mapa-dimensional.yaml`.
- Para cada Programa: extrai entregáveis folha (nível Processo → Entregável).
- Agrupa entregáveis por Fase (alinhada à focus area e ao tipo S/C do projeto).
- Consultor preenche preço/prazo por fase (ou usa estimativas do template).
- Gera `sla-v1.md` com estrutura padronizada.
- Para alterações de escopo: gera `sla-aditivo-NNN.md` sem modificar versões anteriores.

**Estrutura do SLA (template):**

```markdown
# SLA — [Nome do Engagement]
**Versão:** 1.0 | **Data:** YYYY-MM-DD | **Consultor:** | **Cliente:**

## Escopo Acordado
### Programas incluídos
- Programa X — [Descrição] — R$ XXXK — Prazo: N semanas
  - Entregável 1: [Descrição] | Critério de aceite: [Mensurável]
  - Entregável 2: ...

### Fora do escopo (explícito)
- [Item excluído] — Motivo: [Justificativa]

## Condições de Alteração
- Alterações de escopo requerem aditivo formal (sla-aditivo-NNN.md)
- Preço fixo por fase — variações de prazo comunicadas com 7 dias de antecedência
```

**Outputs:** `sla-v{N}.md` (imutável após assinatura), `sla-aditivo-{N}.md`

**Standards Loading (teórico):**
- `practice-guides/pmo-and-processes/pmo-practice-guide-por.pdf` — catálogo de serviços PMO e estrutura de SLA (nível de serviço, métricas, condições de alteração)
- `standards/portfolio-strategy/portfolio-management-standard-4th.pdf` — governança de portfólio e gestão de contratos de serviço
- `docs/Contrato de Prestação de Serviços de Consultoria em Franquia.pdf` — estrutura de cláusulas do contrato real como referência de linguagem jurídica e commercial

---

### Componente 7 — Biblioteca de Templates: `ring/pmo-team/skills/docs/templates/`

**Responsabilidade:** Armazenar templates reutilizáveis de engajamento por segmento, versionados e atualizáveis via lessons learned.

**Estrutura de ficheiros:**

```
ring/pmo-team/skills/docs/templates/
├── franchise/
│   ├── template.yaml          ← estrutura programas + projetos + flows + processos
│   ├── perguntas-escuta.yaml  ← perguntas contextualizadas ao segmento
│   ├── melhores-praticas.md   ← referências para análise de contradições
│   └── CHANGELOG.md           ← histórico de versões (lições aprendidas)
└── {segmento}/
    └── ...
```

**Template `franchise/template.yaml` (estrutura):**

```yaml
segmento: franchise
versao: "1.0"
programas:
  - nome: Modelagem Financeira
    dominio_pmbok_principal: Finanças
    projetos:
      - nome: Diagnóstico e Mapeamento Financeiro As Is
        tipo: S
        flows: [Mapeamento Financeiro As Is, Análise de Exposição a Risco Financeiro, ...]
      - nome: Sistema de Monitoramento Financeiro
        tipo: C
        flows: [Painel de Indicadores, Alertas e Exceções, ...]
  - nome: Modelagem de Governança
    dominio_pmbok_principal: Governança
    projetos: [...]
  - nome: Modelagem Comercial
    dominio_pmbok_principal: Partes interessadas
    projetos: [...]
  - nome: Modelagem Operacional
    dominio_pmbok_principal: Recursos
    projetos: [...]
  - nome: Modelagem Jurídica
    dominio_pmbok_principal: Risco
    projetos: [...]
```

---

## Arquitetura de dados

### Hierarquia de artefatos por engagement

```
ring/pmo-team/skills/docs/engagements/{client-slug}/
├── engagement-context.json       ← estado corrente do engagement
├── mapa-dimensional.yaml         ← output Acto 1 (imutável após aprovação)
├── mapa-dimensional.md           ← versão legível
├── blueprint-estrategico.md      ← output Acto 2 (imutável após aprovação)
├── contradicoes.yaml             ← mapeamento estruturado
├── pmbok-tree.json               ← árvore PMBOK (versionada)
├── pmbok-tree.md                 ← representação legível com diagrama
├── opm-report.md                 ← último relatório OPM
├── opm-indicators.json           ← indicadores correntes
├── sla-v1.md                     ← SLA original (imutável após aprovação)
├── sla-aditivo-001.md            ← aditivos (imutáveis após aprovação)
└── lessons-learned.md            ← lessons learned acumuladas
```

### Versionamento e imutabilidade

- **Imutável após aprovação:** `mapa-dimensional.yaml`, `blueprint-estrategico.md`, `sla-v{N}.md`, `sla-aditivo-{N}.md`
- **Versionado (permite updates):** `pmbok-tree.json`, `opm-indicators.json`, `engagement-context.json`
- **Acumulativo:** `lessons-learned.md`, `opm-report.md`
- **Mecanismo:** git — cada aprovação é um commit com mensagem semântica

---

## Padrões de segurança e dados

- Dados de engagements não são partilhados entre clientes (isolamento por diretório `{client-slug}/`).
- Artefatos imutáveis após aprovação — qualquer alteração requer novo artefato (aditivo ou nova versão).
- Dados de clientes não saem do repositório ring — sem chamadas a APIs externas com dados de engagement.
- Templates não contêm dados de clientes específicos — são genéricos por segmento.

---

## Padrões de integração

### Integração com ring pmo-team plugin

- Todos os agentes seguem o schema de saída padrão do ring pmo-team (`ring:pmo-agent-output-schema`).
- A skill de orquestração usa o padrão `ring:using-pmo-team` para carregar contexto de sessão.
- Anti-rationalization tables obrigatórias em cada agente (per `ring/CLAUDE.md`).

### Integração com Langflow (fase futura — não MVP)

- Os flows de OPM (monitoramento contínuo) serão candidatos a Langflow flows para engajamentos de longa duração.
- O schema PMBOK Tree (JSON) é o contrato de integração — qualquer sistema externo que precisar consumir dados do engagement usará este schema.

---

## Restrições e decisões técnicas pendentes (para Gate 6)

| Decisão | Opções | Gate |
|---------|--------|------|
| Motor de análise de contradições: regras explícitas vs LLM-assisted | A decidir em Gate 6 | Gate 6 |
| Formato de template: YAML puro vs Markdown com frontmatter YAML | A decidir em Gate 6 | Gate 6 |
| Geração de SLA: Markdown puro vs PDF gerado | Markdown (v1); PDF em fase 2 | Gate 6 |
| Storage de indicadores OPM: JSON ficheiro vs Redis/DB | JSON ficheiro (v1 — simplicidade) | Gate 6 |

---

## Gate 3 validation

| Categoria | Requisito | Estado |
|-----------|-----------|--------|
| Todos os domínios do Feature Map mapeados | F-001→F-006 mapeados a componentes | ✅ |
| Todas as features do PRD cobertas | RF-001→RF-006 cobertas por componentes | ✅ |
| Fronteiras de componentes claras | 7 componentes com responsabilidade singular | ✅ |
| Schema de dados definido | PMBOK Tree JSON schema definido | ✅ |
| Sem produtos tecnológicos específicos | Sem menções a LLM vendors, DBs específicas | ✅ |
| Padrões de segurança/isolamento | Isolamento por client-slug, imutabilidade por git | ✅ |
| Rastreabilidade a Feature Map e PRD | Todos os componentes rastreiam a Features e RFs | ✅ |

**Resultado:** ✅ PASS → Gate 6 (Dependency Map)
