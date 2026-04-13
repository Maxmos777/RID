---
feature: frontend-flows
description: Dashboard de listagem de flows (MVP) e futuros componentes relacionados a flows
owner: TechLead
status: in-planning
---

# Frontend Flows — Pre-dev Feature Documentation

## Visão Geral

Esta pasta documenta a evolução do suporte a flows (fluxos) na interface frontend do RID, começando pelo MVP (Listagem de Flows) e expandindo em fases futuras.

**Escopo MVP (GATES 0-5):**
- ✅ Dashboard de listagem de flows por workspace
- ✅ Integração com Langflow via auto-login bridge
- ✅ Multi-tenant isolation
- ✅ Navegação para editor Langflow
- ✅ Persistência de contexto de UI (página, scroll)

**Escopo Futuro (Phase 2+):**
- 📋 Edição de metadata de flows (nome, descrição)
- 📋 Criação de flows via RID UI
- 📋 Deleção de flows
- 📋 Search/filtering avançado
- 📋 Flow versioning e histórico
- 📋 Bulk operations

---

## Estrutura de Gates

| Gate | Status | Arquivo | Descrição |
|------|--------|---------|-----------|
| **0 - Research** | ✅ FINAL | `gate-0-research.md` | Análise Socrática + Q1 RESPONDIDA |
| **0 - Endpoints** | ✅ FINAL | `gate-0-backend-endpoints.md` | Mapeamento completo de APIs (Langflow + RID) |
| **0 - Langflow Deep Dive** | ✅ FINAL | `gate-0-langflow-research.md` | Pesquisa aprofundada session management |
| **0 - Tech Stack Alignment** | ✅ FINAL | `FRONTEND-LIBS-ALIGNMENT.md` | Code patterns + checklist implementação |
| **1 - PRD** | ✅ FINAL | `gate-1-prd.md` | ✅ Refatorado com pesquisa robusta (Q1 + endpoints + tech stack) |
| **2 - Feature Map** | ✅ **FINAL** | `gate-2-feature-map.md` | ✅ 9 features granulares + dependency graph + critical path |
| **3 - TRD** | ✅ FINAL | `gate-3-trd.md` | Technical Requirements Document |
| **4 - Task Breakdown** | ⏳ Próximo | `gate-4-tasks.md` | T-001 a T-009 com subtasks detalhadas |
| **5 - Sign-off** | ⏳ Futuro | `gate-5-signoff.md` | Readiness audit + approval |
| **6 - Dependency Map** | ⏳ Futuro | `gate-6-dependency-map.md` | Grafo de dependências entre tasks |
| **7 - Tasks** | ⏳ Futuro | `gate-7-tasks.md` | Breakdown detalhado de tasks (T-001, T-002, ...) |
| **8 - Subtasks** | ⏳ Futuro | `gate-8-subtasks/` | Decomposição de cada tarefa em subtasks |
| **9 - Delivery Roadmap** | ⏳ Futuro | `gate-9-delivery-roadmap.md` | Timeline e roadmap de entrega |

---

## Histórico de Mudanças

| Data | Evento | Responsável | Status |
|------|--------|-------------|--------|
| 2026-04-11 | GATE 0: Ring brainstorm & research formalizado | Ring | ✅ |
| 2026-04-11 | Q3 Research: Langflow session management | Ring | ✅ |
| 2026-04-11 | Tech Stack: Convergência Langflow | Manual | ✅ |
| 2026-04-11 | GATE 0 Refactored: Intencionalidade + pesquisas | Manual | ✅ FINAL |
| 2026-04-11 | GATE 1: PRD refatorado (pesquisa robusta) | Manual | ✅ FINAL |
| 2026-04-11 | GATE 3: TRD com endpoint spec + component design | Manual | ✅ FINAL |
| 2026-04-11 | Q1 SPIKE RESOLVIDA: Endpoint Langflow confirmado | Ring Explore | ✅ FINAL |
| 2026-04-11 | Backend Endpoints Mapping: All APIs documented | Ring Explore | ✅ FINAL |
| **2026-04-11** | **GATE 2: Feature Map + 9 features granulares + dependency graph** | **Manual** | **✅ FINAL** |
| **2026-04-11** | **Critical Path: 15-21h sequential; 10-14h parallelizado (2 eng)** | **Manual** | **✅ FINAL** |
| Próximo | GATE 4: Task Breakdown (T-001 a T-009 detalhadas) | ⏳ | ⏳ |
| Próximo | GATE 5: Sign-off + readiness audit | ⏳ | ⏳ |

---

## Como Usar Esta Documentação

1. **Para entender o que será feito:** Leia `gate-1-prd.md` (escopo, stories, acceptance criteria)
2. **Para entender como será feito:** Leia `gate-3-trd.md` (arquitetura, componentes, APIs)
3. **Para implementar:** Leia `gate-7-tasks.md` e `gate-8-subtasks/` (instruções passo-a-passo)
4. **Para planejar timeline:** Leia `gate-9-delivery-roadmap.md` (estimativas, critical path)

---

## Contato

Tech Lead: [Será preenchido durante GATE 5 sign-off]
