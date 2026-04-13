---
feature: frontend-flows
gate: 1
date: 2026-04-11
status: final
topology:
  structure: mono-repo
  target_repo: /home/RID
  scope: frontend + backend
  api_pattern: bff
  arch_style: modular_monolith
  edge: reverse_proxy
  edge_router: traefik
research_base:
  - GATE 0: Análise Socrática 6 áreas completada
  - Q1: Endpoint Langflow confirmado (GET /api/v1/projects/{id}/flows/)
  - Q3: Session expiry pattern (proactive refresh + interceptor)
  - Tech Stack: Convergência Langflow v1.8.4 (Zustand 4.5.2, Axios 1.7.4, React Router 6.23.1)
---

# PRD — Dashboard de Flows (MVP Frontend Flows)

## 1. Resumo Executivo

O MVP de Frontend Flows fornece um **dashboard integrado ao RID** para listagem e acesso aos flows do Langflow. Permite que usuários autenticados visualizem seus flows com metadados, naveguem ao editor com sessão preservada, e retornem com contexto de UI restaurado.

**Valor Core:** Unificar a experiência de acesso a flows (antes: URL direta Langflow + re-login; agora: dashboard integrado RID + autenticação centralizada).

**Intenção:** Estabelecer fundação escalável para Phase 2 (criação, edição, bulk operations).

---

## 2. Contexto & Problema

### 2.1 Estado Atual

Flows Langflow acessíveis apenas via:
- ❌ URL direta `http://localhost:7860` (exposição externa)
- ❌ Re-login manual no Langflow (sem reutilização de autenticação RID)
- ❌ Sem visão agregada (usuário não sabe quais flows existem)
- ❌ Sem integração com outras funcionalidades RID (tenants, usuários, etc)

### 2.2 Solução Proposta

Um dashboard em RID que:
- ✅ Lista todos os flows do workspace Langflow do usuário
- ✅ Exibe metadados: nome, descrição, data última atualização
- ✅ Reutiliza autenticação Django + auto-login bridge (ADR-009)
- ✅ Protege acesso via Traefik auth gate (ADR-012)
- ✅ Funciona em domínios públicos multi-tenant (schema isolation)
- ✅ Preserva contexto UI ao navegar e retornar

### 2.3 Personas & Valor

| Persona | Valor Entregue | Critério de Sucesso |
|---------|----------------|-------------------|
| **Admin de Tenant** | Visão agregada de flows em um lugar | Carrega em <2s; mostra todos os flows |
| **Usuário Operacional** | Acesso rápido sem re-autenticar | 1 click → editor Langflow; sessão preservada |
| **Analista de Negócio** | Compreender quais flows existem | Nome + descrição + data em cada card |

---

## 3. Requisitos Funcionais (Baseados em Q1 Respondida)

### RF-001: Listar Flows com Metadados Completos

**User Story:**
```
Como usuário autenticado do RID
Quero visualizar uma lista completa dos flows do meu workspace Langflow
Para compreender quais fluxos existem e seus metadados
```

**Backend API (Q1 — Confirmada):**

Endpoint Langflow confirmado:
```
GET /api/v1/projects/{workspace_id}/flows/
Header: x-api-key: {service_api_key}
Response: { data: [{ id, name, description, updated_at, created_at }] }
```

**RID Backend Proxy (BFF):**
- Endpoint: `GET /api/v1/langflow/flows/list`
- Camadas de validação:
  1. Django session (user autenticado)
  2. Tenant resolution (via X-Tenant-Id ou Host)
  3. TenantMembership (user é membro do tenant)
  4. Workspace_id + API key fetch (Customer model)
  5. Chamada ao Langflow (com x-api-key)

**Frontend Requirements:**

**Acceptance Criteria:**
- [ ] Dashboard exibe grid de flows (12 por página MVP)
- [ ] Cada card mostra:
  - Nome do flow
  - Descrição (se existir)
  - Data última atualização (formatada: "11 de abril, 14:30")
  - Badge/icon com status (opcional MVP)
- [ ] Request a `/api/v1/langflow/flows/list` via Axios (com interceptadores)
- [ ] Apenas flows do workspace autenticado visíveis (validação server-side)
- [ ] Estado de carregamento enquanto fetch
- [ ] Estado vazio com mensagem: "Nenhum flow encontrado"
- [ ] Estado de erro com retry button: "Erro ao carregar flows. Tentar novamente?"

**Tech Stack (Convergência Langflow):**
- **HTTP Client:** Axios 1.7.4 (interceptadores para 401/403)
- **State:** Zustand 4.5.2 (authStore, flowStore)
- **Hook:** `useFlows(config)` — fetch logic
- **Componente:** `FlowsList.tsx` — render grid
- **Componente:** `FlowCard.tsx` — card individual

---

### RF-002: Navegação Segura ao Editor Langflow

**User Story:**
```
Como usuário no dashboard de flows
Quero clicar em "Editar" e ser levado ao editor de flows Langflow
Para modificar lógica do flow sem deixar o RID
```

**Arquitetura (DD-001 Decision):**
- Navegação: `window.location.href = "/flows/{flow_id}"` (same tab)
- Autenticação: Reutiliza auto-login bridge (existe, ADR-009)
- Proteção: Traefik forwardAuth para `/flows/*` (existe, ADR-012)

**Acceptance Criteria:**
- [ ] Botão "Editar no Langflow →" em cada card
- [ ] Click navega para `/flows/{flow_id}`
- [ ] Traefik auth gate valida sessão Django antes de forwarding
- [ ] Usuário permaneça autenticado no Langflow (via auto-login cookie)
- [ ] Nenhum token exposto em URL (seguro)
- [ ] Se sessão expirada: Traefik redireciona para `/login`

**Flow Seguro:**
```
User click "Edit"
→ handleEditFlow(flowId)
  ├─ Save UI context (page, scroll) to sessionStorage
  └─ window.location.href = "/flows/{flowId}"
     └─ Browser: GET /flows/{flowId}
        └─ Traefik: forwardAuth to /internal/auth-check/
           ├─ Django: Validate session (200 OK)
           └─ Forward to Langflow (sessão já validada)
              └─ Langflow: Render editor
```

---

### RF-003: Preservar Contexto ao Retornar

**User Story:**
```
Como usuário navegando entre RID e Langflow
Quero que meu contexto (página, scroll) seja restaurado ao voltar
Para não perder meu ponto no fluxo de trabalho
```

**Arquitetura (DD-008 Decision):**
- Storage: sessionStorage (browser-local, cleared on close)
- Dados persistidos: `{ currentPage, scrollPosition, timestamp }`
- TTL: 30 minutos (graceful degradation)

**Acceptance Criteria:**
- [ ] Antes de navegar: `useFlowsContext.save({ page, scroll })`
- [ ] Ao retornar (back button): `useFlowsContext.restore()`
  - Lê sessionStorage
  - Valida TTL (30 min)
  - Restaura página + scroll
  - Limpa storage
- [ ] Sem exposição de dados sensíveis (apenas UI state)
- [ ] Funciona apenas na mesma aba (sessionStorage isolamento)

---

## 4. Requisitos Não-Funcionais

### Performance

| Métrica | Target | Justificativa |
|---------|--------|--------------|
| **Time to Interactive (TTI)** | <2s | Dashboard responsivo; esperado p95 |
| **Flows API latency (p95)** | <500ms | Incluindo rede + Langflow |
| **JS bundle size** | <200KB gzipped | Fast initial load |
| **Component render** | <100ms | Smooth interaction |

**Validação:** Chrome DevTools Lighthouse; teste em staging com 100 flows.

### Disponibilidade

| Aspecto | Target | Tratamento |
|---------|--------|-----------|
| **Uptime SLA** | 99.5% | Alinhado com RID |
| **Langflow offline** | Graceful degradation | Retorna 503; show error + retry |
| **Sessão expirada** | Automatic logout | Padrão Langflow + overlay Phase 2 |

### Segurança

**Ameaças Mitigadas:**

| Ameaça | Mitigação | Validação |
|--------|-----------|-----------|
| **XSS via flow.name** | React escapa HTML | Testes: sanitization |
| **CSRF** | Django CSRF token | Headers em fetch |
| **Cross-tenant leak** | 4 camadas validação (auth + membership + workspace_id + Langflow) | Testes parametrizados: Tenant A vs B |
| **Session fixation** | sessionStorage isolado | Expires on browser close |
| **Token exposure** | Nenhum token em URLs | Code review + security scan |

**Standards:**
- OWASP Top 10 A01:2021 (Broken Access Control) → 4 camadas
- OWASP Top 10 A03:2021 (Injection) → React XSS protection
- OWASP Top 10 A04:2021 (Insecure Design) → Traefik auth gate

### Acessibilidade (WCAG 2.1 AA)

| Componente | Requisito | Implementação |
|------------|-----------|----------------|
| **Grid/Cards** | Keyboard navigation (Tab/Arrow) | Flexbox + tabindex |
| **Buttons** | Touch targets 44×44px | Tailwind sizing |
| **Contrast** | Text: 4.5:1; UI: 3:1 | Tailwind color classes |
| **Links** | Descriptive aria-label | `aria-label={Flow name}` |
| **Loading state** | Live region announcements | `role="status"` + ARIA |

---

## 5. Scope Definitivo (MVP vs Phase 2+)

### ✅ MVP (Included)

**Funcionalidades:**
- Listagem de flows em grid
- Metadados: nome, descrição, updated_at
- Multi-tenant isolation
- Navegação ao editor (`window.location.href`)
- Persistência de contexto (sessionStorage)
- Estados: loading, error, empty
- Traefik auth gate protection

**Arquitetura:**
- Backend BFF proxy: `/api/v1/langflow/flows/list`
- Frontend: Zustand + Axios + React Router 6.23.1
- DTOs: FlowDTO, FlowsListResponse (Pydantic)
- Tests: TDD RED-GREEN-REFACTOR (>80% coverage)

**Segurança:**
- 4 camadas validação
- Sem tokens em URLs
- Traefik forwardAuth
- ADR compliance (001, 002, 003, 005, 009, 012)

---

### ❌ Out of Scope (Phase 2+)

**Funcionalidades:**
- Criar flows no RID (criados no Langflow, sync futuro)
- Editar metadata de flows (nome, desc) no RID
- Deletar flows via RID
- Search/filtering avançado (tags, status, workflow)
- Flow versioning + histórico
- Bulk operations (duplicar, arquivar múltiplos)
- Flow templates
- Compartilhamento entre tenants
- Custom Langflow theme override
- Modal de session expiry (Langflow pattern; UX polish Phase 2)

**Razão Deferral:**
- MVP foca em 80% valor (listar + acessar editor)
- Tudo mais = nice-to-have, maior complexidade
- Phase 2 pode construir sobre esta fundação

---

## 6. Decisões de Design Consolidadas (com Pesquisa)

| ID | Decisão | Rationale | Fonte |
|----|---------|-----------|-------|
| **DD-001** | Backend proxy (BFF) | Credenciais server-side; CORS handled | GATE 0 analysis |
| **DD-002** | Novo endpoint `/api/v1/langflow/flows/list` | SoC; validação granular | GATE 0 analysis |
| **DD-003** | 4 camadas segurança | Defense-in-depth; ADR compliance | GATE 0 risk analysis |
| **DD-004** | Zustand 4.5.2 + Axios 1.7.4 + React Router 6.23.1 | Convergência Langflow v1.8.4 | Langflow research |
| **DD-005** | TDD obrigatório | RED-GREEN-REFACTOR; 80%+ coverage | GATE 0 testing analysis |
| **DD-006** | MVP: listar + navegar only | Focus; feedback loop rápido | GATE 0 scope analysis |
| **DD-007** | Proactive token refresh (54 min) + 401/403 interceptor | Padrão Langflow (produção) | Langflow research Q3 |
| **DD-008** | sessionStorage bridge (context) | Simples; seguro; MVP suficiente | GATE 0 context decision |
| **DD-009** | Traefik forwardAuth existente (não novo) | Reutiliza ADR-012; menor complexidade | GATE 0 security analysis |

---

## 7. Critério de Aceitação do MVP (Validation Gates)

### Funcional

- [ ] **Dashboard Carrega (<2s):** Chrome DevTools TimelinePerformance
- [ ] **Flows Exibidos Corretamente:** Nome, descrição, updated_at matches Langflow
- [ ] **Click "Editar" Funciona:** Navega para `/flows/{flow_id}` sem erro
- [ ] **Sessão Preservada:** Usuário não precisa re-login no Langflow
- [ ] **Retorno Restaura Contexto:** Back button → página + scroll restaurados
- [ ] **Multi-tenant Isolation:** Tenant A não vê flows de Tenant B (parametrized test)
- [ ] **Estados de UI Corretos:** Loading, error, empty states visíveis

### Não-Funcional

- [ ] **Sem Console Errors:** Zero errors/warnings (exceto libs third-party)
- [ ] **Browser Compatibility:** Chrome 120+, Firefox 121+, Safari 17+ (manual)
- [ ] **WCAG 2.1 AA:** Contraste 4.5:1, touch targets 44×44px
- [ ] **Segurança:** Sem XSS, CSRF, cross-tenant leaks (code review + tests)
- [ ] **Performance:** <2s TTI, <500ms API latency p95

### Testing

- [ ] **Unit Tests:** useFlows, useSessionRefresh, useFlowsContext (>80% coverage)
- [ ] **Component Tests:** FlowsList, FlowCard rendering + interaction
- [ ] **Integration Tests:** `/api/v1/langflow/flows/list` endpoint (pytest)
- [ ] **E2E Test:** Full user journey (init → list → edit → back → restore)
- [ ] **Security Tests:** Parametrized tenant isolation, XSS, CSRF

### ADR Compliance

- [ ] **ADR-001:** `sync_to_async(thread_sensitive=True)` para ORM
- [ ] **ADR-002:** TenantUser public schema; flows external (Langflow)
- [ ] **ADR-003:** Endpoint em FastAPI (`/api/*`)
- [ ] **ADR-005:** TenantAwareBackend + Django session
- [ ] **ADR-009:** Langflow workspace per customer, service API key
- [ ] **ADR-012:** Traefik auth gate `/flows/*`

---

## 8. Roadmap de Releases

### MVP (Esta Release — 2-3 semanas)
- ✅ Dashboard de listagem
- ✅ Navegação ao editor
- ✅ Multi-tenant isolation
- ✅ Context preservation

### Phase 2 (Próximas 4-6 semanas)
- 📋 Criação de flows no RID
- 📋 Edição de metadata (nome, descrição)
- 📋 Deletagem de flows
- 📋 Search/filtering
- 📋 Modal de session expiry (UX)

### Phase 3+ (Futuro)
- 📋 Flow versioning
- 📋 Bulk operations
- 📋 Flow templates
- 📋 Sync com Langflow (criar em Langflow → aparece em RID)
- 📋 Custom Langflow themes

---

## 9. Métricas de Sucesso

| Métrica | Meta | Quando Medir |
|---------|------|--------------|
| **Time to Interactive** | <2s p95 | Post-launch, weekly |
| **Error Rate** | <0.5% (404, 503, etc) | Continuous (Sentry) |
| **Data Leaks** | 0 incidents | Continuous audit |
| **User Satisfaction** | >4/5 stars | Post-launch survey |
| **Adoption** | >50% tenants using | 4 semanas post-launch |
| **Test Coverage** | >80% | Pre-merge gate |

---

## 10. Endpoints API (Baseado em Q1 + Pesquisa)

### Langflow (Internal)

```
GET /api/v1/projects/{workspace_id}/flows/
Header: x-api-key: {service_api_key}
Response: { data: [{ id, name, description, updated_at, created_at }] }
Status: 200, 401, 403, 404, 500
```

**Source:** Q1 RESPONDIDA (gate-0-backend-endpoints.md)

### RID Backend (BFF)

```
GET /api/v1/langflow/flows/list
Headers: X-CSRFToken, Cookie (Django session)
Response: { flows: [...], workspace_id, total_count }
Status: 200, 401, 403, 503
```

**Localização:** `backend/api/routers/langflow_flows.py` (novo arquivo)

### RID Django (Existentes)

```
GET /app/                   → SPA view (LoginRequiredMixin)
GET /internal/auth-check/   → Traefik forwardAuth (ADR-012)
POST /flows/{id}            → Langflow editor (Traefik proxy)
```

---

## 11. Tech Stack Confirmado (via Pesquisa Langflow)

| Lib | Versão | Uso | Status |
|-----|--------|-----|--------|
| **React** | 19.2.1 | Framework | ✅ |
| **TypeScript** | 5.4.5 | Type safety | ✅ |
| **Zustand** | 4.5.2 | State (authStore, flowStore) | ✅ NOVO |
| **Axios** | 1.7.4 | HTTP + interceptadores | ✅ NOVO |
| **React Router** | 6.23.1 | Roteamento | ✅ NOVO |
| **Tailwind CSS** | 3.4.4 | Styling | ✅ |
| **shadcn-ui** | 0.9.4 | Componentes | ✅ NOVO |
| **Vitest** | 2.x | Testes | ✅ |

**Rationale:** Convergência com Langflow v1.8.4 → code familiar para team.

---

## 12. Stakeholders & Sign-off

| Papel | Status | Sign-off Requerido |
|------|--------|-------------------|
| **Product Manager** | ⏳ | GATE 1 PRD approval |
| **Tech Lead** | ⏳ | GATE 1 architecture review |
| **QA Lead** | ⏳ | GATE 1 testing strategy |
| **DevOps/Infra** | ⏳ | GATE 1 deployment checklist |

**Sign-off Gate 1:** Este PRD requer aprovação de todos antes de GATE 2 (Feature Map).

---

## 13. Próximas Etapas (Post-PRD)

1. **GATE 1 Review:** Tech Lead, Product Manager validação
2. **GATE 2 (Feature Map):** Decompor em features granulares
3. **GATE 3 (TRD):** Especificação técnica detalhada
4. **GATE 4 (Task Breakdown):** 9 tasks com dependências
5. **GATE 5 (Sign-off):** Go/No-Go decision + readiness audit

---

## 14. Apêndices

### A. User Flow Diagram

```
1. User: GET /app/flows
2. Django: Validate session (LoginRequiredMixin)
3. Render: SPA template (app-config injected)
4. React: Mount FlowsList
5. Fetch: /api/v1/langflow/flows/list (Axios)
6. Backend: Validate (auth + tenant + membership + workspace)
7. Langflow: GET /api/v1/projects/{id}/flows/ (x-api-key)
8. Response: JSON { flows: [...] }
9. Render: Grid de flows
10. User: Click "Editar"
11. Navigate: window.location.href = /flows/{id}
12. Traefik: forwardAuth check
13. Langflow: Render editor
14. User: Click back
15. React: Restore page + scroll from sessionStorage
```

### B. Security Model

**4 Camadas Validação:**
1. **Django Session:** Usuario autenticado?
2. **TenantMembership:** Usuario membro do tenant?
3. **Workspace_id:** Workspace vinculado ao tenant?
4. **Langflow x-api-key:** API key válida para workspace?

Falha em qualquer camada → acesso negado.

### C. Referências

- GATE 0: `gate-0-research.md` — Análise Socrática completa
- Q1: `gate-0-backend-endpoints.md` — Endpoints confirmados
- Tech Stack: `FRONTEND-LIBS-ALIGNMENT.md` — Code patterns
- ADRs: `docs/adr/ADR-*.md` — Architecture decisions

---

**PRD Status: FINAL** ✅  
**Pronto para: GATE 1 Review + Sign-off**  
**Pesquisa Base:** GATE 0 + Q1-Q3 + Langflow research consolidada
