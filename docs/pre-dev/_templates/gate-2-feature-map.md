---
feature: {feature-slug}
gate: 2
date: {date}
status: draft
# Valores possíveis: draft | review | approved
prd_ref: {caminho-gate-1-prd}
ux_criteria_ref: {caminho-ux-criteria}
topology:
  scope: {scope}
  # Valores possíveis: fullstack | backend | frontend | infra
  api_pattern: {api-pattern}
  # Valores possíveis: bff | rest | graphql | rpc
---

# Feature map — {feature-name}

## Overview

| Campo | Valor |
|-------|-------|
| PRD | `{caminho-gate-1-prd}` (Gate 1 — {status-prd}) |
| UX Criteria | `{caminho-ux-criteria}` |
| Wireframes | `{caminho-wireframes-dir}` |
| Status | Draft — Gate 2 |
| Última actualização | {date} |

---

## Feature inventory

<!-- Classificar features em: Core (MVP bloqueante), Supporting (MVP complementar), Enhancement (pós-MVP).
     Cada feature recebe um ID F-NNN sequencial. -->

### Core (MVP — bloqueia tudo o resto)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-001 | {nome-feature-core-1} | {descricao} | {valor} | — | {lista-de-features-bloqueados} |
| F-002 | {nome-feature-core-2} | {descricao} | {valor} | F-001 | {lista-de-features-bloqueados} |
| F-003 | {nome-feature-core-3} | {descricao} | {valor} | F-001 | {lista-de-features-bloqueados} |

### Supporting (MVP — habilita ou complementa o core)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-004 | {nome-feature-supporting-1} | {descricao} | {valor} | F-001 | — |
| F-005 | {nome-feature-supporting-2} | {descricao} | {valor} | {dependencias} | — |

### Enhancement (Fase 2 — pós-MVP)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-006 | {nome-feature-enhancement} | {descricao} | {valor} | {dependencias} | — |

---

## Domain groupings

<!-- Agrupar features por domínio lógico. Cada domínio deve ter:
     - Propósito claro
     - Features que pertence
     - O que "owns" (responsabilidades)
     - O que "provides" para outros domínios
     - O que "consumes" de outros domínios ou sistemas
     - Integration points -->

### Domínio 1 — {nome-dominio-1}

**Propósito:** {descricao-do-proposito-do-dominio}

**Features:** {lista-de-features-deste-dominio}

**Owns:**
- {responsabilidade-1}
- {responsabilidade-2}

**Provides para outros domínios:**
- {output-1} → {dominio-destino}

**Consumes:**
- {input-1} (de {sistema-ou-dominio-origem})

**Integration points:**
- ← {sistema-externo-1} ({descricao})
- → {dominio-2}: {descricao-do-que-fornece}

---

### Domínio 2 — {nome-dominio-2}

**Propósito:** {descricao-do-proposito-do-dominio}

**Features:** {lista-de-features-deste-dominio}

**Owns:**
- {responsabilidade-1}
- {responsabilidade-2}

**Provides para outros domínios:**
- {output-1} → {dominio-destino}

**Consumes:**
- {input-1} (de {dominio-origem})

**Integration points:**
- ← {dominio-1}: {descricao}
- → {sistema-externo}: {descricao}

---

<!-- Adicionar mais domínios conforme necessário -->

## User journeys

<!-- Mapear os principais fluxos de utilizador cross-domínio.
     Referenciar os user flows detalhados do Gate 1.5. -->

### Journey 1 — {nome-journey-1}

<!-- Exemplo: "Utilizador autenticado acede ao editor" -->

```
{actor} → {passo-1} → {passo-2} → {passo-3} → {resultado}
```

*Referência: {caminho-user-flow-gate-1.5}*

### Journey 2 — {nome-journey-2}

```
{actor} → {passo-1} → {passo-2} → {resultado}
```

---

## Dependency matrix

<!-- Matriz de dependências entre features. X = "depende de". -->

|  | F-001 | F-002 | F-003 | F-004 | F-005 |
|--|:-----:|:-----:|:-----:|:-----:|:-----:|
| **F-001** | — | | | | |
| **F-002** | X | — | | | |
| **F-003** | X | | — | | |
| **F-004** | X | | | — | |
| **F-005** | X | X | | X | — |

---

## Phasing strategy

### MVP (Gate 3 → implementação imediata)

**Features incluídos:** {lista-features-mvp}

**Rationale:** {justificativa-do-que-entra-no-mvp}

### Fase 2 (pós-MVP)

**Features incluídos:** {lista-features-fase-2}

**Rationale:** {justificativa-do-que-fica-para-fase-2}

---

## Gate 2 — Validation checklist

| Verificação | Estado |
|-------------|--------|
| [ ] Todos os RF do PRD mapeados para features F-NNN | PENDENTE |
| [ ] Features Core identificados e separados de Supporting/Enhancement | PENDENTE |
| [ ] Domínios lógicos definidos com ownership claro | PENDENTE |
| [ ] Dependency matrix sem dependências circulares | PENDENTE |
| [ ] User journeys cross-domínio documentados | PENDENTE |
| [ ] Phasing strategy definida com rationale | PENDENTE |
| [ ] Features Fase 2 claramente separados do MVP | PENDENTE |

**Resultado: {PASS | FAIL} — {justificativa}**
