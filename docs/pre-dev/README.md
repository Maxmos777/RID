# Pre-dev — Índice de features

> Índice de todos os features em pré-desenvolvimento ou prontos para implementação.
> Actualizar manualmente sempre que um feature mudar de status ou completar um gate.

| Feature | Status | Gates completos | Início | Fim previsto |
|---------|--------|----------------|--------|--------------|
| [rid-langflow-single-entry](rid-langflow-single-entry/gate-1-prd.md) | ✅ Implementation Ready | G0–G9 | 2026-04-06 | 2026-04-15 |

---

## Status possíveis

| Status | Significado |
|--------|-------------|
| 📋 Planning | Feature identificado; Gate 0 ainda não iniciado |
| 🔄 In Pre-Dev | Gates em progresso (G0–G8) |
| ✅ Implementation Ready | Todos os gates necessários concluídos; pronto para dev |
| 🚀 In Development | Em implementação activa |
| ✅ Done | Implementado e validado em produção |

---

## Estrutura de gates

| Gate | Nome | Artefacto |
|------|------|-----------|
| G0 | Research & Brainstorm | `gate-0-research.md`, `gate-0-brainstorm.md` |
| G1 | PRD | `gate-1-prd.md` |
| G1.5 | Design Validation | `gate-1.5-design-validation.md` |
| G2 | Feature Map | `gate-2-feature-map.md` |
| G3 | TRD | `gate-3-trd.md` |
| G4 | API Design | `gate-4-api-design.md` *(quando aplicável)* |
| G5 | Data Model | `gate-5-data-model.md` *(quando aplicável)* |
| G6 | Dependency Map | `gate-6-dependency-map.md` |
| G7 | Tasks | `gate-7-tasks.md` |
| G8 | Subtasks | `gate-8-subtasks/{task-id}/` |
| G9 | Delivery Roadmap | `gate-9-delivery-roadmap.json` |

---

## Templates

Templates para novos features disponíveis em [`_templates/`](_templates/).
