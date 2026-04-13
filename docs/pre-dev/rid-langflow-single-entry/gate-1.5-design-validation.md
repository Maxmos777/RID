---
feature: rid-langflow-single-entry
gate: 1.5
date: 2026-04-05
author: ring:product-designer
verdict: DESIGN VALIDATED
prd_ref: docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md
ux_criteria_ref: docs/pre-dev/rid-langflow-single-entry/gate-1.5-ux-criteria.md
wireframes_ref: docs/pre-dev/rid-langflow-single-entry/gate-1.5-wireframes/
---

# Design validation — Entrada única autenticada para o editor de fluxos

## Artefactos de design validados

| Artefacto | Caminho | Estado |
|-----------|---------|--------|
| PRD | `docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md` | Aprovado (Gate 1) |
| UX Criteria | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-ux-criteria.md` | VALIDATED |
| User flows | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-wireframes/user-flows.md` | Completo (4 flows) |
| Wireframe — página de erro | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-wireframes/error-page.yaml` | Completo |
| Wireframe — fluxo de redirect | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-wireframes/auth-redirect-flow.yaml` | Completo |

---

## Checklist de validação

### Problema e personas

| Verificação | Estado |
|-------------|--------|
| Problema validado com evidência (não pressuposto) | PASS |
| Causa raiz identificada (topologia de rede — `:7861` exposto) | PASS |
| Referência interna documentada (RockItDown como padrão) | PASS |
| Duas personas documentadas (Ana + Bruno) | PASS |
| Jobs to be done definidos por persona (3 jobs) | PASS |

### Flows de utilizador

| Verificação | Estado |
|-------------|--------|
| Flow 1: acesso autenticado (happy path) com diagrama Mermaid | PASS |
| Flow 2: utilizador não autenticado — redirect para login | PASS |
| Flow 3: sessão expira durante uso do editor | PASS |
| Flow 4: editor indisponível — página de erro | PASS |
| State machine do auth gate documentada | PASS |
| Paths de erro em todos os flows | PASS |
| Entry points e exit points documentados | PASS |

### Wireframes

| Verificação | Estado |
|-------------|--------|
| `error-page.yaml` com componentes e estados completos | PASS |
| `error-page.yaml` com ASCII prototype desktop e mobile | PASS |
| `auth-redirect-flow.yaml` com 3 passos e decisão de estado transitório | PASS |
| UI Library declarada nos dois wireframes | PASS |
| Responsive behavior documentado | PASS |

### Acessibilidade

| Verificação | Estado |
|-------------|--------|
| WCAG 2.1 AA declarado | PASS |
| Contraste 4.5:1 especificado | PASS |
| Navegação por teclado documentada | PASS |
| Screen reader: `role="alert"`, `aria-hidden`, `aria-label` especificados | PASS |
| `aria-live` para estados transitórios | PASS |

### Issues do PRD Issues Log

| Severidade | Issue | Estado |
|------------|-------|--------|
| HIGH | Sessão expirada durante uso do editor | RESOLVED |
| HIGH | Estado transitório antes do redirect HTTP | RESOLVED |
| MEDIUM | CTAs da página de erro não especificadas | Endereçado nos wireframes |
| MEDIUM | Authorization vs authentication — utilizador sem permissão | Promovido para TRD |
| MEDIUM | Preservação do `next` param para URLs com hash fragments | Promovido para TRD |
| LOW | Redirect para raiz vs fluxo específico — edge case | Promovido para TRD |

> Issues MEDIUM e LOW não bloqueiam o design. São decisões de implementação para o TRD.

### Issues Resolvidas — Revisão arquitectural pós-Gate 3

| Severidade | Issue | Estado |
|------------|-------|--------|
| CRITICAL | Proxy não existia no docker-compose | RESOLVED — Traefik adicionado como container Docker com forwardAuth |
| CRITICAL | Overlay (DD-001) em conflito com comportamento 302 do proxy | RESOLVED — Overlay activado por heartbeat periódico, não por resposta do proxy |
| CRITICAL | Sub-request quebrava resolução de tenant (django-tenants) | RESOLVED — Host header original configurado no forwardAuth do Traefik |

---

## Decisões de design

### DD-001 — Sessão expirada: overlay via heartbeat periódico

**Decisão:** O shell React faz polling periódico (heartbeat a cada 2-3 minutos) ao Auth Check Endpoint (`GET /internal/auth-check/`). Se receber 401, apresenta o overlay "Sessão expirada" com botão "Entrar novamente" antes de qualquer acção do utilizador. O Edge Router (Traefik) continua a retornar 302 para navegação inicial sem sessão — comportamento correcto para primeiro acesso.

**Alternativa rejeitada:** Interceptar respostas 401 do proxy durante uso activo — impossível porque o Traefik/nginx retorna sempre 302 (redirect) para qualquer 401 do Auth Check, nunca 401 directamente ao cliente browser durante navegação.

**Impacto no TRD:** Auth Check Endpoint deve ser acessível para pedidos do shell React (não apenas sub-requests internos do Traefik). Heartbeat deve ser cancelado quando o utilizador sai do editor.

---

### DD-002 — Estado transitório: HTTP 302 directo

**Decisão:** O gate responde com HTTP 302 imediatamente ao detectar sessão ausente. Sem página intermédia.

**Alternativa rejeitada:** Micro-página com spinner — flash de branco < 100ms é aceitável.

**Impacto no TRD:** Sem componente adicional a implementar para este estado.

---

### DD-003 — Página de erro: dois CTAs com identidade RID

**Decisão:** "Tentar novamente" (primário — GET `/flows/`, não `reload()`) + "Voltar ao painel" (link secundário). Identidade visual RID, mensagem em pt-BR.

**Impacto no TRD:** Página deve ser servida pelo servidor RID sem dependência de assets do Langflow.

---

### DD-004 — UI Library: raw React 18 + inline styles + plain CSS

**Decisão:** Auto-detectado do projecto. Sem biblioteca de componentes externa.

---

### DD-005 — Acessibilidade: WCAG 2.1 AA

**Decisão:** Aplicado a todos os componentes novos deste feature. O editor Langflow não é auditado.

**Impacto no TRD:** Contraste mínimo 4.5:1, touch targets 44×44px em mobile.

---

## Veredicto

```
DESIGN VALIDATED — pronto para Gate 3 (TRD)
```

Artefactos completos: problema validado, duas personas, quatro user flows com Mermaid e state machine, dois wireframes YAML com prototypes e acessibilidade, critérios UX com todos os estados. Issues HIGH resolvidas. Issues MEDIUM/LOW promovidas para TRD.
