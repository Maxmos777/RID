---
feature: rid-langflow-single-entry
gate: 9
date: 2026-04-06
type: delivery-roadmap
---

# Roteiro de Entrega — Entrada única autenticada para o editor de fluxos (RID)

---

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Feature | rid-langflow-single-entry |
| Gate | 9 — Delivery Planning |
| Data de início | 2026-04-06 (Segunda-feira) |
| Data de conclusão prevista | 2026-04-15 (Quarta-feira) |
| Duração total (com buffer) | 6,5 dias úteis |
| Estimativa AI total | 26h |
| Horas ajustadas (×1.5) | 39,0h |
| Horas calendário (÷0.90) | 43,33h |
| Dias calendário (÷8h/dia) | 5,41 dias |
| Buffer de contingência | 15% → +1 dia → 6,5 dias |
| Equipa | 1 developer (solo) |
| Multiplicador de validação humana | 1.5× (standard) |
| Taxa de utilização | 90% |
| Cadência de entrega | Contínua (milestones por capacidade) |
| Score de confiança | 89/100 — ALTO |

---

## Cálculo de Capacidade

### Fórmula aplicada

```
adjusted_hours  = ai_estimate × 1.5
calendar_hours  = adjusted_hours ÷ 0.90
calendar_days   = calendar_hours ÷ 8   (1 developer, 8h/dia)
```

### Tabela de cálculo por tarefa

| Task | Título | AI Est. | Ajustado (×1.5) | Calendário (÷0.9) | Dias (÷8) |
|------|--------|---------|-----------------|-------------------|-----------|
| T-001 | Traefik container + docker-compose | 4h | 6,0h | 6,67h | 0,83d |
| T-002 | Django proxy header settings | 2h | 3,0h | 3,33h | 0,42d |
| T-003 | Auth Check Endpoint /internal/auth-check/ | 5h | 7,5h | 8,33h | 1,04d |
| T-004 | Error Page Template + Django view | 4h | 6,0h | 6,67h | 0,83d |
| T-005 | Session Expiry Overlay + heartbeat hook | 5h | 7,5h | 8,33h | 1,04d |
| T-006 | Integration + E2E tests | 6h | 9,0h | 10,0h | 1,25d |
| **TOTAL** | | **26h** | **39,0h** | **43,33h** | **5,41d** |

**Com buffer de contingência de 15%:**
5,41d × 1,15 = 6,22d → arredondado para **6,5 dias úteis**

---

## Sequência de Execução

### Ordem óptima para 1 developer (minimiza bloqueios)

Com equipa solo, todas as tarefas são sequenciais. A ordem é determinada pela análise de dependências para desbloquear o caminho crítico o mais cedo possível:

1. **T-002** primeiro (0,42d) — mais rápido, desbloqueia T-003 imediatamente
2. **T-001** segundo (0,83d) — desbloqueia T-004 e permite integração
3. **T-003** terceiro (1,04d) — desbloqueia T-005
4. **T-004** quarto (0,83d) — T-001 já concluído
5. **T-005** quinto (1,04d) — T-003 já concluído
6. **T-006** último (1,25d) — todas as dependências satisfeitas

### Tabela de datas por tarefa

| Task | Título | Início | Fim | Duração | Dependências | Estado |
|------|--------|--------|-----|---------|--------------|--------|
| T-002 | Django proxy header settings | 2026-04-06 | 2026-04-06 | 0,42d | — | Pronto |
| T-001 | Traefik container + docker-compose | 2026-04-07 | 2026-04-07 | 0,83d | — | Pronto |
| T-003 | Auth Check Endpoint | 2026-04-08 | 2026-04-09 | 1,04d | T-002 | Bloqueado |
| T-004 | Error Page Template + Django view | 2026-04-09 | 2026-04-09 | 0,83d | T-001 | Bloqueado |
| T-005 | Session Expiry Overlay + heartbeat | 2026-04-10 | 2026-04-13 | 1,04d | T-003 | Bloqueado |
| T-006 | Integration + E2E tests | 2026-04-13 | 2026-04-15 | 1,25d | T-001, T-003, T-004, T-005 | Bloqueado |

> Nota: T-005 inicia na Sexta 10/04 e transborda para Segunda 13/04 (fim-de-semana não conta). T-006 arranca Segunda 13/04.

---

## Milestones

### Milestone 1 — Infraestrutura pronta
**Data alvo: 2026-04-07**
**Tarefas:** T-002 + T-001

| Item | Detalhe |
|---|---|
| Deliverable | Traefik v3.3.6 em execução, Django proxy-ready, porta 7861 fechada externamente |
| Critério de aceitação | `curl -I http://localhost/flows/` → 302; porta 7861 não exposta; `docker compose config` válido |
| Dependências | Nenhuma (ambas as tarefas sem hard deps) |

---

### Milestone 2 — Auth gate activo
**Data alvo: 2026-04-09**
**Tarefas:** T-003 + T-004

| Item | Detalhe |
|---|---|
| Deliverable | Endpoint `/internal/auth-check/` live; página de erro RID funcionando; acesso não autenticado redireccionado para login |
| Critério de aceitação | Pedido sem sessão → 302 para login; tenant errado → 403; Langflow indisponível → página de erro RID |
| Dependências | Milestone 1 concluído |

---

### Milestone 3 — Experiência completa do utilizador
**Data alvo: 2026-04-10**
**Tarefas:** T-005

| Item | Detalhe |
|---|---|
| Deliverable | Overlay de sessão expirada activo no browser; heartbeat a cada 2 minutos |
| Critério de aceitação | Sessão expirada → overlay aparece sem perder contexto; botão "Iniciar sessão" abre tab de login; heartbeat faz GET `/internal/auth-check/` cada 2 min |
| Dependências | T-003 concluído (Milestone 2) |

---

### Milestone 4 — Validado e pronto para produção
**Data alvo: 2026-04-15**
**Tarefas:** T-006

| Item | Detalhe |
|---|---|
| Deliverable | Todos os testes de integração e E2E a passar; feature confirmado production-ready |
| Critério de aceitação | Suite completa verde: acesso não autenticado, expiração de sessão, isolamento de tenant, Langflow indisponível |
| Dependências | Milestones 1 + 2 + 3 concluídos (T-001, T-003, T-004, T-005) |

---

## Análise do Caminho Crítico

### Grafo de dependências

```
T-002 ──► T-003 ──► T-005 ──► T-006
                              ▲
T-001 ──► T-004 ──────────────┘
```

### Cadeia de dependências mais longa

```
T-002 → T-003 → T-005 → T-006
0,42d + 1,04d + 1,04d + 1,25d = 3,75 dias
```

Esta é a cadeia crítica por dependência pura.

### Cadeia alternativa

```
T-001 → T-004 → T-006
0,83d + 0,83d + 1,25d = 2,91 dias
```

### Duração mínima do projecto (1 developer, sequencial)

Com 1 developer, paralelização não é possível. A duração real é a soma de todas as tarefas:

**5,41 dias úteis → 6,5 dias com buffer de 15%**

### Tarefas no caminho crítico

| Task | No caminho crítico? | Motivo |
|------|---------------------|--------|
| T-001 | Não | Cadeia paralela (2,91d vs 3,75d) |
| T-002 | **Sim** | Início da cadeia crítica |
| T-003 | **Sim** | Desbloqueia T-005 |
| T-004 | Não | Cadeia mais curta |
| T-005 | **Sim** | Desbloqueia T-006 |
| T-006 | **Sim** | Conclusão final |

---

## Alocação de Recursos

| Recurso | Tipo | Tarefas | Horas totais (calendário) |
|---------|------|---------|--------------------------|
| Developer (solo) | Full-stack + DevOps | T-001, T-002, T-003, T-004, T-005, T-006 | 43,33h |

Com cadência contínua e 1 developer, não existe sobreposição de tarefas. O developer actua como:
- **DevOps** em T-001 (docker-compose, Traefik)
- **Backend** em T-002, T-003, T-004 (Django, auth, templates)
- **Frontend** em T-005 (React, overlay, heartbeat)
- **QA** em T-006 (integração, E2E)

---

## Gestão de Riscos

### Risco 1 — Integração Traefik com django-tenants
**Nível:** MÉDIO
**Tarefas:** T-001

| Campo | Detalhe |
|---|---|
| Impacto | Labels Traefik para django-tenants com Host header são novidade neste codebase; má configuração quebra resolução de tenant |
| Probabilidade | Média — configuração documentada em ST-001-01, mas ainda por validar em ambiente real |
| Mitigação | ST-001-01 fornece YAML exacto; testar com `docker-compose up` localmente antes de prosseguir para T-003 |
| Sinal de alerta | `curl` para `/flows/` retorna 500 em vez de 302 após T-001 concluído |

---

### Risco 2 — Testes E2E em CI (Docker-in-Docker)
**Nível:** ALTO
**Tarefas:** T-006

| Campo | Detalhe |
|---|---|
| Impacto | Testes E2E requerem stack docker-compose completa (Traefik + Django + Langflow); CI pode não suportar Docker-in-Docker |
| Probabilidade | Alta — ambientes CI geridos raramente expõem Docker socket |
| Mitigação | Separar testes unitários dos testes de integração docker-compose; CI faz gate nos unitários; integração corre localmente ou em runner dedicado |
| Sinal de alerta | CI falha com "Cannot connect to Docker daemon" em T-006 |

---

### Risco 3 — HeaderFirstTenantMiddleware e X-Forwarded-Host
**Nível:** MÉDIO
**Tarefas:** T-001 + T-002

| Campo | Detalhe |
|---|---|
| Impacto | `HeaderFirstTenantMiddleware` pode não ler `X-Forwarded-Host` correctamente através do Traefik, causando falha de resolução de tenant |
| Probabilidade | Média — depende de configuração correcta de `ALLOWED_HOSTS` e `USE_X_FORWARDED_HOST` em Django |
| Mitigação | Testar com `curl -H "X-Forwarded-Host: app.rid.example.com"` imediatamente após T-001 + T-002 completos antes de avançar para T-003 |
| Sinal de alerta | Django retorna 400 Bad Request ou tenant errado em pedidos via Traefik |

---

## Linha do Tempo (ASCII Gantt)

```
Semana 1: 2026-04-06 a 2026-04-10
Semana 2: 2026-04-13 a 2026-04-15

Dia:       Seg 06  Ter 07  Qua 08  Qui 09  Sex 10  Seg 13  Ter 14  Qua 15
           ──────  ──────  ──────  ──────  ──────  ──────  ──────  ──────
T-002      [████]
T-001              [████]
T-003                      [████   ─]
T-004                              [████]
T-005                                      [████   ─]
T-006                                              [████   ████   ████]
                                                                   ▲
                                                              FIM + BUFFER

Legenda:
  [████]  tarefa activa
  [────]  transbordo para dia seguinte
  ▲       data de conclusão com buffer
```

---

## Pressupostos e Restrições

### Pressupostos

| # | Pressuposto |
|---|-------------|
| 1 | O developer trabalha 8 horas úteis por dia, 5 dias por semana |
| 2 | Não há feriados entre 2026-04-06 e 2026-04-15 |
| 3 | O ambiente de desenvolvimento local suporta docker-compose com Traefik |
| 4 | As subtarefas (ST-XXX) de cada task estão definidas e acessíveis ao developer |
| 5 | As credenciais e variáveis de ambiente necessárias estão disponíveis (`.env.example`) |
| 6 | A taxa de utilização de 90% reflecte interrupções normais (reuniões, code review, comunicação) |
| 7 | O multiplicador 1.5× cobre revisão de código, testes manuais e correcções menores |
| 8 | CI/CD pipeline existente; apenas a suite de testes é nova |

### Restrições

| # | Restrição |
|---|-----------|
| 1 | Equipa de 1 developer — sem paralelização de tarefas |
| 2 | Cadência contínua — sem sprints fixos; milestones por capacidade |
| 3 | Budget de tempo fixo derivado das estimativas AI com multiplicadores padrão |
| 4 | Testes E2E podem não correr em CI se Docker-in-Docker não estiver disponível |

---

## Definição de Feito por Milestone

### Milestone 1 — Infraestrutura pronta (2026-04-07)
- [ ] `docker compose --profile langflow up` inicia sem erros
- [ ] `docker compose config` valida sem warnings
- [ ] Porta 7861 não está exposta no host (`ss -tlnp | grep 7861` retorna vazio)
- [ ] `curl -I http://localhost/flows/` retorna 302 (sem sessão)
- [ ] `.env.example` actualizado com `LANGFLOW_BASE_URL` e `LANGFLOW_CORS_ORIGINS`
- [ ] `USE_X_FORWARDED_HOST = True` e `SECURE_PROXY_SSL_HEADER` configurados em Django

### Milestone 2 — Auth gate activo (2026-04-09)
- [ ] GET `/internal/auth-check/` com sessão válida → 200 com headers `X-Auth-User` e `X-Auth-Tenant`
- [ ] GET `/internal/auth-check/` sem sessão → 302 para `/accounts/login/`
- [ ] GET `/internal/auth-check/` com tenant errado → 403
- [ ] Acesso a `/flows/` sem sessão → redireccionado para login (via Traefik forwardAuth)
- [ ] Langflow indisponível → página de erro RID servida (não erro genérico de proxy)
- [ ] View de erro Django registada em `urls.py` e template `langflow_error.html` criado

### Milestone 3 — Experiência completa do utilizador (2026-04-10)
- [ ] Hook `useHeartbeat` faz GET `/internal/auth-check/` cada 2 minutos
- [ ] Sessão expirada (401/302 do heartbeat) → overlay `SessionExpiredOverlay` aparece
- [ ] Overlay não interrompe o estado da aplicação (sem refresh forçado)
- [ ] Botão "Iniciar sessão" no overlay abre tab de login
- [ ] `HeartbeatProvider` envolve o layout principal da aplicação React
- [ ] Testes unitários React para hook e overlay a passar

### Milestone 4 — Validado e pronto para produção (2026-04-15)
- [ ] Suite de testes de integração Django a passar (pytest, mínimo 80% cobertura nas vistas novas)
- [ ] Testes E2E Playwright a passar localmente: acesso não autenticado, expiração de sessão, isolamento de tenant, Langflow indisponível
- [ ] `docker scout cves traefik:v3.3.6` documentado no PR
- [ ] PR description inclui checklist de segurança preenchida
- [ ] Feature flag ou configuração de deploy documentada se aplicável

---

## Score de Confiança

| Factor | Pontos | Racional |
|--------|--------|----------|
| Clareza de dependências | 28/30 | Todas as 6 tarefas têm deps claras; um edge case (ordenação T-004 vs T-003) resolvido na análise |
| Realismo de capacidade | 22/25 | 1 developer a 90% de capacidade AI; realista para esta stack |
| Caminho crítico validado | 23/25 | Grafo de dependências completo; cadeia clara T-002→T-003→T-005→T-006 |
| Mitigação de riscos | 16/20 | 3 riscos identificados com mitigações accionáveis; risco CI/CD classificado HIGH |
| **TOTAL** | **89/100** | **CONFIANÇA ALTA** |

> Score de 89/100 indica que o plano é robusto e as estimativas são fiáveis. O principal factor de incerteza é o comportamento do CI/CD com Docker-in-Docker (T-006), mitigado pela separação de suites de teste.
