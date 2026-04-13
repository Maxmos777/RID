---
feature: {feature-slug}
gate: 1
date: {date}
status: draft
# Valores possíveis: draft | review | approved
confidence: {confidence-percentage}
# Percentagem de 0–100 representando confiança no escopo e viabilidade
topology:
  structure: {structure}
  # Valores possíveis: monorepo | multi-repo
  target_repo: {target-repo-path}
  reference_repo: {reference-repo-path}
  # Remover reference_repo se não houver repositório de referência
---

# PRD — {feature-name}

## Resumo executivo

<!-- 2-4 frases: qual o problema central, qual a solução proposta, e qual o valor de negócio.
     Responde a: "o que estamos construindo e porquê?" -->

{resumo-executivo}

---

## Problema

<!-- Descrever o problema actual em detalhe. Incluir:
     - Estado actual (o que acontece hoje)
     - Impacto (bullets com consequências concretas)
     - Evidência (referência à pesquisa Gate 0) -->

{descricao-do-problema-actual}

**Impacto:**
- {impacto-1}
- {impacto-2}
- {impacto-3}

**Evidência (pesquisa Gate 0 — `{caminho-gate-0}`):**
- {evidencia-1}
- {evidencia-2}

---

## Personas

### 1. {persona-1-nome} ({persona-1-tipo})

<!-- Tipo: ex. "enterprise", "power user", "admin", "end user" -->

**Papel:** {descricao-do-papel}

**Objetivos:**
- {objetivo-1}
- {objetivo-2}
- {objetivo-3}

**Frustrações actuais:**
- {frustracao-1}
- {frustracao-2}
- {frustracao-3}

---

### 2. {persona-2-nome} ({persona-2-tipo})

**Papel:** {descricao-do-papel}

**Objetivos:**
- {objetivo-1}
- {objetivo-2}
- {objetivo-3}

**Frustrações actuais:**
- {frustracao-1}
- {frustracao-2}

---

## Requisitos de produto (o quê, não o como)

<!-- Cada RF deve ter: descrição, valor de negócio, e critério de aceitação mensurável.
     Formato: RF-NNN onde NNN começa em 001 e incrementa sequencialmente. -->

### RF-001 — {nome-do-requisito}

{descricao-do-requisito}

**Valor:** {valor-de-negocio}
**Critério de aceitação:** {criterio-mensuravel}

---

### RF-002 — {nome-do-requisito}

{descricao-do-requisito}

**Valor:** {valor-de-negocio}
**Critério de aceitação:** {criterio-mensuravel}

---

### RF-003 — {nome-do-requisito}

{descricao-do-requisito}

**Valor:** {valor-de-negocio}
**Critério de aceitação:** {criterio-mensuravel}

---

<!-- Adicionar mais RF conforme necessário -->

## Métricas de sucesso

<!-- Tabela com métricas mensuráveis. Baseline = estado actual (mesmo que "não medido").
     Alvo = valor a atingir após deploy. Prazo = quando medir. -->

| Métrica | Baseline | Alvo | Prazo |
|---------|----------|------|-------|
| {metrica-1} | {baseline-1} | {alvo-1} | {prazo-1} |
| {metrica-2} | {baseline-2} | {alvo-2} | {prazo-2} |
| {metrica-3} | {baseline-3} | {alvo-3} | {prazo-3} |

---

## Escopo

### Incluído

<!-- Lista explícita do que está dentro do escopo deste feature/MVP -->

- {item-incluido-1}
- {item-incluido-2}
- {item-incluido-3}

### Excluído (explicitamente)

<!-- Lista explícita do que NÃO está no escopo. Ser específico evita escopo deslizante. -->

- {item-excluido-1} *(razão: {motivo})*
- {item-excluido-2} *(fase 2 futura)*
- {item-excluido-3}

---

## Perguntas abertas

<!-- Questões que ainda não foram decididas no Gate 1. Questões técnicas de implementação
     vão para o TRD (Gate 3), não aqui. -->

{perguntas-abertas}

---

## Pressupostos de negócio

<!-- O que se assume como verdade para este PRD ser válido. -->

- {pressuposto-1}
- {pressuposto-2}
- {pressuposto-3}

---

## Dependências de negócio

<!-- O que precisa acontecer fora do time de produto/dev para este feature ter sucesso. -->

- {dependencia-1}
- {dependencia-2}

---

## Referências

<!-- Links para artefactos relacionados: pesquisa Gate 0, padrões de referência, ADRs existentes, etc. -->

- Pesquisa Gate 0: `{caminho-gate-0-research}`
- Brainstorm: `{caminho-gate-0-brainstorm}`
- Padrão de referência: `{caminho-padrao-referencia}` — {descricao-do-padrao}
