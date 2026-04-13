# Registo de Partes Interessadas (Stakeholder Register)

**Projecto:** RID Platform
**Data:** 2026-04-03
**Versão:** 1.0

---

## Matriz de Partes Interessadas

| ID | Parte Interessada | Papel | Interesse | Influência | Envolvimento Actual | Envolvimento Desejado |
|---|---|---|---|---|---|---|
| S1 | Product Owner | Decisão de produto | Funcionalidades que entregam valor ao cliente final; roadmap | Alto | Baixo | Alto |
| S2 | Tech Lead | Liderança técnica | Qualidade arquitectural, ADRs, decisões de stack | Alto | Alto | Alto |
| S3 | Engenheiro Backend | Implementação | Qualidade do código, testes, migrations, DX | Médio | Alto | Alto |
| S4 | Engenheiro Frontend | Implementação frontend | SPA, integração com API, UX | Médio | Baixo | Alto (Gate 3) |
| S5 | DevOps / SRE | Operações | Docker, CI/CD, observabilidade, deployment | Médio | Baixo | Médio (Gate 5) |
| S6 | Cliente Final (Tenant) | Utilizador da plataforma | Onboarding rápido, Langflow funcional, dados isolados | Baixo | Nenhum | Médio (beta) |
| S7 | Stripe | Fornecedor de billing | Integração correcta da API, compliance PCI-DSS | Baixo | Indirecto | Baixo |
| S8 | Langflow (LangChain Inc.) | Fornecedor de AI workflows | Versão estável, API consistente | Baixo | Indirecto | Baixo |

---

## Estratégia de Envolvimento

| Parte Interessada | Estratégia | Frequência | Canal |
|---|---|---|---|
| S1 — Product Owner | Consultar em cada gate de produto (M2, M4, M6) | Por milestone | Apresentação de status + demo |
| S2 — Tech Lead | Revisão de ADRs, gate reviews, aprovação de planos | Contínuo | PRs, ADR reviews, gate reports |
| S3 — Engenheiro Backend | Colaboração diária em implementação | Diário | PRs, pair programming |
| S4 — Engenheiro Frontend | Briefing de API contracts antes de Phase 4 | Por fase | Docs de API, OpenAPI spec |
| S5 — DevOps / SRE | Envolver em Gate 5 (Production Readiness) | Por gate | Makefile, docker-compose, infra docs |
| S6 — Cliente Final | Beta tester em M6 (staging deployment) | Por milestone | Feedback sessions |
| S7 — Stripe | N/A — integração via SDK | N/A | Documentação oficial |
| S8 — Langflow | Monitorizar changelog e breaking changes | Mensal | GitHub releases |

---

## Requisitos de Comunicação

| Quem recebe | O quê | Quando | Formato |
|---|---|---|---|
| S1, S2 | Gate status report | Em cada gate completado | `pmo/docs/05-change-log.md` + demo |
| S2, S3 | ADR decay audit | End Stage Assessment de cada gate | `scripts/audit-adrs.sh` output |
| S3, S4 | API contracts | Antes de Phase 4 (Frontend) | OpenAPI spec em `/api/docs` |
| S5 | Infrastructure state | Gate 5 | Production Readiness Audit report |

---

## Registo de Alterações

| Versão | Data | Alteração | Autor |
|---|---|---|---|
| 1.0 | 2026-04-03 | Versão inicial — Gate 4 | ring:governance-specialist |

---

*Referência: PMBOK 7, Secção 13 — Stakeholder Management*
