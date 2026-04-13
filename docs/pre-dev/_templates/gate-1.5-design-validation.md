---
feature: {feature-slug}
gate: 1.5
date: {date}
author: {agent-ou-autor}
# Exemplo: ring:product-designer
verdict: {verdict}
# Valores possíveis: DESIGN VALIDATED | DESIGN REJECTED | PENDING REVISIONS
prd_ref: {caminho-gate-1-prd}
ux_criteria_ref: {caminho-ux-criteria}
wireframes_ref: {caminho-wireframes-dir}
---

# Design validation — {feature-name}

## Artefactos de design validados

<!-- Tabela com todos os artefactos produzidos neste gate e o respectivo estado -->

| Artefacto | Caminho | Estado |
|-----------|---------|--------|
| PRD | `{caminho-gate-1-prd}` | {estado-prd} |
| UX Criteria | `{caminho-ux-criteria}` | {estado-ux-criteria} |
| User flows | `{caminho-user-flows}` | {estado-user-flows} |
| Wireframe — {nome-wireframe-1} | `{caminho-wireframe-1}` | {estado-wireframe-1} |
| Wireframe — {nome-wireframe-2} | `{caminho-wireframe-2}` | {estado-wireframe-2} |

---

## Checklist de validação

### Problema e personas

| Verificação | Estado |
|-------------|--------|
| [ ] Problema validado com evidência (não pressuposto) | PENDENTE |
| [ ] Causa raiz identificada | PENDENTE |
| [ ] Referência interna documentada (padrão existente) | PENDENTE |
| [ ] Personas documentadas (mínimo 2) | PENDENTE |
| [ ] Jobs to be done definidos por persona | PENDENTE |

### Flows de utilizador

| Verificação | Estado |
|-------------|--------|
| [ ] Flow 1: happy path (utilizador autenticado) com diagrama | PENDENTE |
| [ ] Flow 2: utilizador não autenticado — redirecionamento | PENDENTE |
| [ ] Flow 3: {flow-3-nome} — {descricao-breve} | PENDENTE |
| [ ] Flow 4: {flow-4-nome} — {descricao-breve} | PENDENTE |
| [ ] State machine do gate principal documentada | PENDENTE |
| [ ] Paths de erro em todos os flows | PENDENTE |
| [ ] Entry points e exit points documentados | PENDENTE |

### Wireframes

| Verificação | Estado |
|-------------|--------|
| [ ] `{wireframe-1-ficheiro}` com componentes e estados completos | PENDENTE |
| [ ] `{wireframe-1-ficheiro}` com prototype ASCII desktop e mobile | PENDENTE |
| [ ] `{wireframe-2-ficheiro}` com {conteudo-esperado} | PENDENTE |
| [ ] UI Library declarada em todos os wireframes | PENDENTE |
| [ ] Responsive behavior documentado | PENDENTE |

### Acessibilidade

| Verificação | Estado |
|-------------|--------|
| [ ] WCAG 2.1 AA declarado | PENDENTE |
| [ ] Contraste 4.5:1 especificado | PENDENTE |
| [ ] Navegação por teclado documentada | PENDENTE |
| [ ] Screen reader: roles ARIA e labels especificados | PENDENTE |
| [ ] `aria-live` para estados transitórios | PENDENTE |

### Issues do PRD Issues Log

<!-- Listar todas as issues abertas do PRD e o seu estado neste gate.
     Issues HIGH devem ser resolvidas antes do veredicto VALIDATED.
     Issues MEDIUM e LOW podem ser promovidas para o TRD. -->

| Severidade | Issue | Estado |
|------------|-------|--------|
| HIGH | {issue-1} | PENDENTE |
| HIGH | {issue-2} | PENDENTE |
| MEDIUM | {issue-3} | PENDENTE |
| LOW | {issue-4} | PENDENTE |

> Issues MEDIUM e LOW não bloqueiam o design. São decisões de implementação para o TRD.

---

### Issues Resolvidas — Revisão arquitectural pós-Gate 3

<!-- Preencher após Gate 3. Issues descobertas na validação arquitectural que exigiram
     revisão das decisões de design. Listar aqui para rastreabilidade. -->

| Severidade | Issue | Estado |
|------------|-------|--------|
| {severidade} | {issue-descoberta-em-gate-3} | RESOLVED — {resolucao} |

---

## Decisões de design

<!-- Uma secção por decisão de design (DD-NNN). Cada decisão deve incluir:
     - O que foi decidido
     - A alternativa que foi rejeitada e porquê
     - O impacto no TRD (Gate 3) -->

### DD-001 — {nome-da-decisao}

**Decisão:** {descricao-da-decisao}

**Alternativa rejeitada:** {alternativa} — {motivo-da-rejeicao}

**Impacto no TRD:** {impacto}

---

### DD-002 — {nome-da-decisao}

**Decisão:** {descricao-da-decisao}

**Alternativa rejeitada:** {alternativa} — {motivo-da-rejeicao}

**Impacto no TRD:** {impacto}

---

### DD-003 — {nome-da-decisao}

**Decisão:** {descricao-da-decisao}

**Impacto no TRD:** {impacto}

---

<!-- Adicionar DD-NNN conforme necessário -->

## Veredicto

```
{verdict} — {justificativa-do-veredicto}
```

<!-- Exemplo: "DESIGN VALIDATED — pronto para Gate 3 (TRD)"
     Ou: "DESIGN REJECTED — issues HIGH não resolvidas: {lista}" -->

{artefactos-completos-e-observacoes-finais}
