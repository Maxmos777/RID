---
feature: framework-thinking-agent-model
gate: 1
date: 2026-04-09
status: draft
confidence: 88
design_doc: ring/pmo-team/docs/plans/2026-04-09-framework-thinking-agent-model-design.md
topology:
  scope: methodology
  structure: single-repo
  target_repo: /home/RID/ring
  plugin: pmo-team
  research_ref: ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-research.md
  research_appendix: ring/pmo-team/skills/docs/pre-dev/pmo/appendix-wbs-franquia.md
---

# PRD — Framework Thinking Agent Model (ring pmo-team)

## Resumo executivo

Consultorias que operam em contextos de alta complexidade (expansão comercial, franquias, transformação organizacional) carecem de uma metodologia estruturada e replicável que unifique a escuta do cliente, a análise estratégica e a orquestração de programas de trabalho. Este documento define os requisitos para o **Framework Thinking Agent Model** — um padrão de engajamento de consultoria amplificado por agentes de IA, baseado no PMBOK 8ª Edição, que transforma a interação com o cliente em artefatos executáveis, rastreáveis e versionáveis, desde a estratégia até ao nível atómico de processo.

---

## Problema

A consultoria tradicional produz artefatos desconectados — apresentações, planeamentos, manuais — que não têm continuidade operacional nem rastreabilidade até à estratégia. O consultor parte do zero a cada engagement, sem metodologia que garanta coerência entre o que o cliente diz e o que a organização realmente precisa de fazer.

**Impacto observado:**
- Blueprints estratégicos produzidos sem evidência das contradições entre visão do cliente e realidade operacional.
- Programas de trabalho criados sem hierarquia clara (Estratégia → Portfólio → Programa → Projeto → Flow → Processo) — rastreabilidade estratégica ausente.
- Artefatos de engagement não reutilizáveis entre clientes do mesmo segmento (ex.: todas as franchises de alimentação têm os mesmos programas-tipo).
- Ausência de SLA contratual alinhado ao nível de serviço real de cada engagement, gerando expectativas desalinhadas.
- Sem mecanismo de monitoramento contínuo do alinhamento entre execução e estratégia definida (OPM — Organizational Project Management).

**Evidência (Gate 0 — `gate-0-research.md` + anexo):**
- Case de referência: proposta de 120k para consultoria de franquia de alimentos — estrutura de 5 programas (Financeiro, Governança, Comercial, Operacional, Jurídico), cada um com projetos sazonais (S) e contínuos (C), flows e processos mapeados em detalhe (**árvore completa:** [`appendix-wbs-franquia.md`](appendix-wbs-franquia.md)).
- Modelo de 3 actos: (1) escuta exclusiva, (2) análise estratégica em bastidores, (3) pulverização de ações e fluxos operacionais.
- PMBOK 8 como meta-linguagem de negócios: 6 Princípios + 7 Domínios de Desempenho + 5 Focus Areas aplicados a cada nível da hierarquia.

---

## Personas

### 1. Consultor Estratégico

**Papel:** Conduz engagements de consultoria com clientes de média e grande dimensão, tipicamente em contextos de expansão, franchising, transformação organizacional ou estruturação de PMO.

**Objetivos:**
- Conduzir a primeira interação com o cliente com perguntas estruturadas que extraiam visão, objetivos, desafios, oportunidades, riscos e custos/benefícios.
- Produzir um blueprint estratégico que explicite contradições entre a visão do cliente e a realidade operacional, sem expor o processo analítico ao cliente no primeiro momento.
- Entregar programas de trabalho hierarquicamente coerentes (alinhados à estratégia) com cronograma, SLA e artefatos por fase.
- Reutilizar estruturas de programas comprovadas (ex.: template de franquia) como ponto de partida, adaptando ao contexto específico do cliente.

**Frustrações atuais:**
- Cada engagement começa do zero — sem padrão de perguntas, sem estrutura de programas reutilizável.
- O blueprint estratégico fica "na cabeça do consultor" sem artefato formal que outros possam auditar ou dar continuidade.
- Dificuldade em explicar ao cliente por que determinados programas são necessários — sem rastreabilidade da decisão até à contradição identificada na escuta.
- SLAs acordados verbalmente, sem documento que registe o que foi acordado e a que preço/prazo.

---

### 2. PMO Lead (interno ao cliente)

**Papel:** Responsável por gerir a execução dos programas de trabalho definidos pelo consultor, garantindo que os projetos estejam alinhados com a estratégia da organização.

**Objetivos:**
- Receber programas de trabalho claramente definidos, com projetos, flows e processos devidamente hierarquizados.
- Monitorar o alinhamento estratégico em tempo real: se um projeto diverge da estratégia, saber imediatamente.
- Ter dashboards e relatórios que mostrem o estado do portfólio por domínio (Financeiro, Governança, Comercial, Operacional, Jurídico).
- Adaptar o metodologia a novos contextos (ex.: novo franqueado, nova unidade) sem depender do consultor para cada iteração.

**Frustrações atuais:**
- Programas de trabalho entregues sem estrutura padronizada — difícil de monitorar de forma homogénea.
- Sem indicadores de alinhamento estratégico — só sabe que algo está errado quando o problema já é visível.
- Relatórios manuais — gasta tempo compilando informação em vez de analisar.

---

### 3. Cliente / Franqueador (utilizador indireto)

**Papel:** Organização que contrata a consultoria para estruturar ou expandir o seu modelo de negócio (ex.: franqueador que quer lançar rede de franquias).

**Objetivos:**
- Receber um plano de expansão coerente, com cronograma realista e investimento estimado por fase.
- Ter artefatos concretos e acionáveis em mãos (manuais, contratos, modelos financeiros, planos de marketing).
- Perceber claramente o que a consultoria vai entregar, em que prazo e a que custo — sem surpresas.
- Ter confiança de que a estrutura proposta é uma prática comprovada de mercado, não uma solução inventada especificamente para ele.

**Frustrações atuais:**
- Propostas comerciais sem detalhamento de entregáveis por fase — difícil avaliar valor recebido vs valor pago.
- Metodologia da consultoria opaca — não sabe se o que está a receber é padrão de mercado ou improvisado.
- Sem mecanismo para verificar, por conta própria, se a execução está alinhada ao que foi prometido.

---

## Requisitos de produto

### RF-001 — Protocolo de Escuta Estruturada (Acto 1)

O framework fornece um protocolo guiado de perguntas para a primeira interação com o cliente, cobrindo obrigatoriamente seis dimensões: (1) visão do negócio, (2) objetivos estratégicos, (3) desafios atuais, (4) oportunidades identificadas, (5) riscos percebidos, (6) estimativa de benefícios e custos envolvidos.

**Valor:** O consultor conduz a escuta de forma estruturada e replicável, garantindo que nenhuma dimensão crítica é omitida e que o artefato resultante (transcrição + mapa dimensional) é auditável.

**Critério de aceitação:**
- O protocolo produz um artefato estruturado (mapa dimensional do cliente) ao final da sessão de escuta.
- O mapa cobre as 6 dimensões independentemente do segmento ou contexto do cliente.
- O processo de escuta não expõe ao cliente a análise de contradições (que ocorre no Acto 2).

---

### RF-002 — Blueprint Estratégico por Contradições (Acto 2)

A partir do mapa dimensional (RF-001) e de referências de melhores práticas do segmento, o framework gera um blueprint estratégico que: (a) identifica alinhamentos entre a visão do cliente e a realidade operacional; (b) mapeia contradições entre o que o cliente diz querer e o que as práticas de mercado indicam ser necessário; (c) propõe uma estrutura de prioridades estratégicas.

**Valor:** O consultor chega à segunda reunião com o cliente com um artefato de análise fundamentado — não uma opinião — que justifica cada programa de trabalho proposto.

**Critério de aceitação:**
- O blueprint identifica, no mínimo, 3 contradições entre visão e realidade por engagement.
- Cada contradição mapeia para um ou mais programas na árvore PMBOK (RF-003).
- O blueprint é um artefato versionável — versões anteriores são preservadas para auditoria.

---

### RF-003 — Construção da Árvore PMBOK (Acto 3 — Estrutura)

O framework constrói e mantém a hierarquia completa de gestão do engagement:

```
Estratégia
  └── Portfólio
        └── Programa (por domínio: Financeiro, Governança, Comercial, Operacional, Jurídico)
              └── Projeto (sazonal S ou contínuo C)
                    └── Flow
                          └── Processo
```

Cada nó carrega: domínios PMBOK relevantes, focus area ativa (Iniciar/Planejar/Executar/Monitorar/Encerrar), artefatos associados e rastreabilidade até ao nível estratégico.

**Valor:** PMO Lead e consultor têm visibilidade completa da hierarquia de trabalho e do alinhamento estratégico em qualquer momento.

**Critério de aceitação:**
- A árvore respeita a hierarquia de 6 níveis (Estratégia → Processo) sem exceções.
- Cada nó tem pelo menos: nome, domínio(s) PMBOK, focus area ativa, estado (Iniciar/Planejar/Executar/Monitorar/Encerrar).
- É possível navegar da Estratégia até ao Processo e vice-versa em qualquer artefato.
- A árvore suporta projetos sazonais (S) e contínuos (C) com comportamentos distintos de monitoramento.

---

### RF-004 — Templates de Engajamento Reutilizáveis

O framework mantém uma biblioteca de templates de programas por segmento de cliente (ex.: franquia de alimentos, consultoria jurídica, expansão comercial). Cada template contém a estrutura pré-definida de Programa → Projeto → Flow → Processo, adaptável ao contexto específico.

**Valor:** O consultor não começa do zero — parte de um template validado do segmento, adaptando o que é específico do cliente. O case de franquia (`appendix-wbs-franquia.md`, síntese em `gate-0-research.md`) é o primeiro template de referência.

**Critério de aceitação:**
- Existe pelo menos um template completo para o segmento de franquia (com os 5 programas do case de referência).
- Um novo engagement baseado num template é configurável em menos de uma sessão de trabalho.
- Templates são versionáveis — um template pode evoluir sem quebrar engagements já em andamento que o usam como base.

---

### RF-005 — OPM Flow Management (Acto 3 — Execução)

O framework fornece mecanismos de monitoramento contínuo do alinhamento entre a execução dos projetos e a estratégia definida, incluindo: indicadores de alinhamento por domínio, alertas de desvio estratégico, ciclos de melhoria contínua (lessons learned → atualização de manuais → refinamento de contratos).

**Valor:** PMO Lead identifica desvios estratégicos antes de se tornarem problemas operacionais; lições aprendidas alimentam a melhoria contínua dos templates.

**Critério de aceitação:**
- O sistema produz indicadores de alinhamento estratégico para pelo menos os 7 Domínios de Desempenho PMBOK.
- Desvios são classificados por severidade (crítico, alerta, observação).
- Lições aprendidas de um engagement podem ser incorporadas ao template do segmento.

---

### RF-006 — SLA Contratual por Engagement

O framework produz um documento de SLA (Service Level Agreement) por engagement, explicitando: (a) escopo acordado (programas incluídos e excluídos), (b) entregáveis por fase com critérios de aceite, (c) preço/prazo por programa, (d) condições de alteração de escopo.

**Valor:** Cliente e consultor têm expectativas alinhadas desde o início — o SLA é o artefato de referência para resolução de disputas e gestão de mudanças.

**Critério de aceitação:**
- O SLA mapeia cada programa da árvore PMBOK a entregáveis concretos com critério de aceite mensurável.
- O SLA é gerado automaticamente a partir da árvore PMBOK do engagement (RF-003).
- Alterações de escopo produzem um SLA aditivo versionado, não substituem o original.

---

## Métricas de sucesso

| Métrica | Baseline | Alvo | Prazo |
|---------|----------|------|-------|
| Tempo para produzir blueprint estratégico (por engagement) | ≥ 3 dias | ≤ 4 horas | Após 1ª implementação |
| Cobertura das 6 dimensões de escuta em cada engagement (%) | Não medido | 100% | Após adoção do protocolo |
| Reutilização de templates entre engagements do mesmo segmento (%) | 0% (zero templates) | ≥ 80% | 90 dias pós-lançamento |
| Satisfação do consultor com estrutura do engagement (CSAT) | Não medido | ≥ 4.2/5 | 60 dias pós-adoção |
| Disputas de escopo por ausência de SLA formal | Não medido | 0 após adoção | Contínuo |
| Alinhamento estratégico detectado por OPM (desvios identificados antes de virar problema) | 0% (manual) | ≥ 70% | 120 dias pós-deploy |

---

## Escopo

### Incluído

- Protocolo estruturado de escuta do cliente (6 dimensões — Acto 1)
- Motor de geração de blueprint estratégico por contradições (Acto 2)
- Construção e manutenção da árvore PMBOK (6 níveis — Acto 3)
- Biblioteca de templates de engajamento por segmento (franchise como template de referência)
- Mecanismo de OPM: monitoramento de alinhamento estratégico por domínio
- Geração de SLA contratual a partir da árvore PMBOK
- Suporte a projetos sazonais (S) e contínuos (C) com comportamentos distintos
- Versionamento de blueprints, árvores e SLAs
- Ciclo de melhoria contínua: lessons learned → templates

### Excluído (explicitamente)

- Gestão financeira dos projetos (controlo de custos reais, pagamentos) — fora do escopo do padrão metodológico
- CRM de prospecção de clientes — antecede o engagement
- Execução direta dos processos operacionais do cliente — o framework estrutura e monitoriza, não executa
- Interface gráfica de gestão de portfólio (dashboard visual) — fase 2
- Integração com ferramentas externas de gestão de projetos (Jira, Asana, Monday) — fase 2
- Suporte multi-idioma na v1 — português (pt-BR) apenas

---

## Pressupostos de negócio

- O consultor tem acesso ao Ring framework (ring pmo-team) e ao Langflow para execução dos agentes.
- O cliente aceita partilhar informações de negócio suficientes para alimentar o protocolo de escuta (RF-001).
- O segmento de franquia de alimentos (case em `appendix-wbs-franquia.md`, documentado no Gate 0) é representativo o suficiente para validar o padrão metodológico antes de expandir para outros segmentos.
- O PMBOK 8ª Edição é aceite como referência metodológica pelo cliente ou pelo consultor.

---

## Dependências de negócio

- Validação do template de franquia com pelo menos um engagement real antes de declarar o padrão estável.
- Definição de critérios de aceite para "alinhamento estratégico" com uma organização PMO real (para calibrar os indicadores do RF-005).

---

## Perguntas abertas

Todas as decisões de implementação técnica (arquitetura de agentes Ring, estrutura de Langflow flows, schema de dados PMBOK tree) são deliberadamente excluídas deste documento e serão resolvidas no TRD (Gate 3).

---

## Referências

- Pesquisa Gate 0: `ring/pmo-team/skills/docs/pre-dev/pmo/gate-0-research.md`
- Anexo (árvore case franquia): `ring/pmo-team/skills/docs/pre-dev/pmo/appendix-wbs-franquia.md`
- PMBOK® Guide – Eighth Edition (6 Princípios, 7 Domínios, 5 Focus Areas)
- PMI — *Standard for Organizational Project Management* (`opm-standard-volume-1.pdf`) — estratégia organizacional e estrutura OPM
- Case de referência: Proposta de franquia 120k (detalhe no anexo; síntese no Gate 0)
- Ring pmo-team skills: `ring/pmo-team/skills/`
