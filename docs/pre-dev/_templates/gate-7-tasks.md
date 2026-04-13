---
feature: {feature-slug}
gate: 7
date: {date}
topology:
  structure: {structure}
  # Valores possíveis: monorepo | multi-repo
  backend_path: {backend-path}
  frontend_path: {frontend-path}
---

# Task Breakdown — {feature-name}

## Summary table

<!-- Tabela de resumo de todas as tasks. Tipos possíveis: backend | frontend | shared/infra | shared/qa
     Status: ⏸️ Pending | 🔄 In Progress | ✅ Done | ❌ Blocked
     Confidence: High | Medium | Low -->

| Task | Title | Type | Est. Hours | Confidence | Blocks | Status |
|------|-------|------|-----------|-----------|--------|--------|
| T-001 | {titulo-task-001} | {tipo} | {estimativa}h | {confianca} | {lista-de-tasks-bloqueadas} | ⏸️ Pending |
| T-002 | {titulo-task-002} | {tipo} | {estimativa}h | {confianca} | {lista-de-tasks-bloqueadas} | ⏸️ Pending |
| T-003 | {titulo-task-003} | {tipo} | {estimativa}h | {confianca} | {lista-de-tasks-bloqueadas} | ⏸️ Pending |
| T-004 | {titulo-task-004} | {tipo} | {estimativa}h | {confianca} | — | ⏸️ Pending |

**Total estimated effort:** {total}h
**Critical path:** {lista-de-tasks-no-caminho-critico}

---

## Business Deliverables

<!-- Descrever o valor de negócio de cada task em linguagem não técnica.
     "O que o utilizador/negócio ganha quando esta task está completa?" -->

| Task | Deliverable (plain language) |
|------|------------------------------|
| T-001 | {descricao-valor-negocio-task-001} |
| T-002 | {descricao-valor-negocio-task-002} |
| T-003 | {descricao-valor-negocio-task-003} |
| T-004 | {descricao-valor-negocio-task-004} |

---

## T-001 — {titulo-task-001}

**Target:** {tipo-de-target}
<!-- Valores: backend | frontend | shared/infra | shared/qa -->
**Working Directory:** `{caminho-do-working-directory}`
**Agent:** `{ring-agent}`
<!-- Exemplos: ring:backend-engineer-python | ring:frontend-engineer-react | ring:devops-engineer -->
**Size:** {tamanho} ({estimativa}h)
<!-- Tamanhos: XS (<1h) | S (1-2h) | M (3-5h) | L (6-9h) | XL (10h+) -->

**Deliverable:** {descricao-tecnica-precisa-do-entregavel}

---

### Scope

**Includes:**
<!-- Lista detalhada e precisa do que está incluído. Nível de detalhe suficiente
     para que um agente saiba exatamente o que implementar. -->
- {item-incluido-1}
- {item-incluido-2}
- {item-incluido-3}
- {item-incluido-4}

**Excludes:**
<!-- Lista explícita do que NÃO é escopo desta task (evita escopo deslizante). -->
- {item-excluido-1} ({referencia-a-task-responsavel-se-aplicavel})
- {item-excluido-2}
- {item-excluido-3}

---

### Success Criteria

<!-- Critérios verificáveis e objectivos. Separar em Functional, Technical, Quality. -->

**Functional:**
- {criterio-funcional-1}
- {criterio-funcional-2}
- {criterio-funcional-3}

**Technical:**
- {criterio-tecnico-1}
- {criterio-tecnico-2}
- {criterio-tecnico-3}

**Quality:**
- {criterio-qualidade-1}
- {criterio-qualidade-2}

---

### User Value

{descricao-do-valor-para-o-utilizador-ou-negocio}

### Technical Value

{descricao-do-valor-tecnico-como-fundacao-para-outras-tasks}

### Technical Components (TRD)

<!-- Referenciar os componentes do TRD (Gate 3) que esta task implementa -->

- {componente-trd-1}
- {componente-trd-2}

---

### Dependencies

**Blocks:** {lista-de-tasks-bloqueadas-por-esta}

**Requires:** {lista-de-tasks-que-esta-depende} *(ou "None" se for primeira task)*

**Optional:** {dependencias-opcionais}

---

### Effort Estimate

<!-- Desagregar a estimativa por sub-item para maior transparência -->

| Sub-item | Est. | Notes |
|----------|------|-------|
| {sub-item-1} | {estimativa} | {nota} |
| {sub-item-2} | {estimativa} | {nota} |
| {sub-item-3} | {estimativa} | {nota} |

**Total: {total}h — Confidence: {confianca}** ({justificativa-da-confianca})

---

### Testing Strategy

<!-- Lista de como esta task será testada. Incluir comandos quando possível. -->

- {metodo-teste-1}
- {metodo-teste-2}
- {metodo-teste-3}

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| {risco-1} | {probabilidade} | {impacto} | {mitigacao} |
| {risco-2} | {probabilidade} | {impacto} | {mitigacao} |

---

### Definition of Done

<!-- Checklist binária. Cada item deve ser verificável objectivamente.
     Esta lista alimenta o gate de entrega (Gate 9). -->

- [ ] {item-done-1}
- [ ] {item-done-2}
- [ ] {item-done-3}
- [ ] {item-done-4}
- [ ] {item-done-5}

---

## T-002 — {titulo-task-002}

**Target:** {tipo-de-target}
**Working Directory:** `{caminho-do-working-directory}`
**Agent:** `{ring-agent}`
**Size:** {tamanho} ({estimativa}h)

**Deliverable:** {descricao-tecnica-precisa-do-entregavel}

---

### Scope

**Includes:**
- {item-incluido-1}
- {item-incluido-2}

**Excludes:**
- {item-excluido-1}

---

### Success Criteria

**Functional:**
- {criterio-funcional-1}

**Technical:**
- {criterio-tecnico-1}
- {criterio-tecnico-2}

**Quality:**
- {criterio-qualidade-1}

---

### User Value

{descricao-do-valor}

### Technical Value

{descricao-do-valor-tecnico}

### Technical Components (TRD)

- {componente-trd-1}

---

### Dependencies

**Blocks:** {lista-de-tasks-bloqueadas}

**Requires:** {tasks-requeridas}

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| {sub-item-1} | {estimativa} | {nota} |
| {sub-item-2} | {estimativa} | {nota} |

**Total: {total}h — Confidence: {confianca}** ({justificativa})

---

### Testing Strategy

- {metodo-teste-1}
- {metodo-teste-2}

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| {risco-1} | {probabilidade} | {impacto} | {mitigacao} |

---

### Definition of Done

- [ ] {item-done-1}
- [ ] {item-done-2}
- [ ] {item-done-3}

---

<!-- Repetir o bloco T-NNN para cada task adicional -->
