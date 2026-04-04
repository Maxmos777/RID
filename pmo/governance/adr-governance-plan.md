# ADR Governance Plan — RID Platform

**Date:** 2026-04-03
**Status:** Approved for execution
**Agent:** ring:governance-specialist
**Projecto:** RID Platform — SaaS multi-tenant (Django 6 + FastAPI + django-tenants)
**Relacionado com:** `2026-04-03-rid-platform-architecture.md`, `2026-04-03-code-review-fixes.md`

---

## Governance Summary

O projecto RID Platform concluiu o **Gate 3** (execução + testes verdes). O End Stage Assessment
identificou **6 decisões arquitecturais críticas** tomadas durante a implementação que não foram
formalmente documentadas. Todas existem como comentários inline no código ou como notas implícitas
nos planos de implementação — o que é insuficiente para governance.

**Decisão de gate:** O Gate 4 (primeira feature de produto) **NÃO DEVE iniciar** sem que os ADRs
P0 (ADR-001 e ADR-002) estejam no estado `Accepted`. Os ADRs P1 podem ser concluídos em paralelo
com Gate 4, mas antes do Gate 5. Os ADRs P2 e P3 têm prazo até ao final do Gate 5.

**Risco imediato sem ADRs P0:** Um engenheiro novo ou uma refactorização de performance pode
remover o `thread_sensitive=True` em `deps.py` (ADR-001) ou mover utilizadores para o schema do
tenant (ADR-002) — ambos causam falhas silenciosas em produção que não são detectadas por testes
unitários standard.

---

## Gate Assessment

| Gate | Nome | Estado | Dependência ADR |
|---|---|---|---|
| Gate 0 | Arquitectura base | ✅ Concluído | ADR-001, 002, 003 (código existe, ADR falta) |
| Gate 1 | DevOps / Docker | ✅ Concluído | ADR-006 (código existe, ADR falta) |
| Gate 2 | SRE / Observabilidade | ✅ Concluído | — |
| Gate 3 | Testes unitários + verde | ✅ Concluído | ADR-004, 005 (código existe, ADR falta) |
| **Gate 3.5** | **ADR Governance** | **🔴 A executar** | Todos os 6 ADRs |
| Gate 4 | Primeira feature produto | 🔒 Bloqueado por ADR-001, ADR-002 | |
| Gate 5 | Integração + billing | 🔒 Pendente | ADR-004, ADR-005 devem existir antes |

**O Gate 3.5 é este plano.** A sua execução desbloqueia Gate 4 parcialmente.

---

## ADR Governance Framework

### 1. Estrutura de pastas

```
/home/RID/
└── docs/
    ├── plans/          ← planos de implementação (input)
    └── adr/            ← decisões arquitecturais (output permanente)
        ├── README.md   ← índice vivo de todos os ADRs
        ├── ADR-001-sync-to-async-tenant-isolation.md
        ├── ADR-002-users-in-public-schema.md
        ├── ADR-003-hybrid-django-fastapi-asgi.md
        ├── ADR-004-provision-tenant-service-layer.md
        ├── ADR-005-tenant-aware-auth-backend.md
        └── ADR-006-postgres-port-5433-docker.md
```

**Regra de nomes:** `ADR-{NNN}-{slug-kebab-case}.md`
- `NNN` — número de 3 dígitos, sequencial, nunca reutilizado
- `slug` — máximo 6 palavras, descreve a decisão (não a tecnologia)
- Sem datas no nome de ficheiro (a data fica dentro do documento)

### 2. Template MADR (Markdown Architectural Decision Records)

Cada ficheiro ADR segue **exactamente** este template:

```markdown
# ADR-{NNN} — {Título da Decisão}

**Data:** YYYY-MM-DD
**Estado:** Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}
**Autores:** {nomes ou roles}
**Revisores:** {nomes ou roles}
**Contexto de código:** `{ficheiro(s) principais afectados}`

---

## Contexto

[O que estava a acontecer no projecto que forçou esta decisão?
Descreve as forças em tensão, as restrições, e o estado antes da decisão.
Máximo 150 palavras.]

## Decisão

[A decisão tomada. Uma frase clara, afirmativa, no presente.
Exemplo: "Usamos sync_to_async com thread_sensitive=True para ..."]

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| {alternativa A} | {razão} |
| {alternativa B} | {razão} |

## Consequências Positivas

- {consequência 1}
- {consequência 2}

## Consequências Negativas / Trade-offs

- {trade-off 1}
- {trade-off 2}

## Compliance

[Como verificar que esta decisão está a ser seguida.
Pode incluir: nome de test, linter rule, comment obrigatório, PR checklist item.]

## Referências

- `{ficheiro:linha}` — implementação de referência
- `{link}` — documentação externa relevante
```

### 3. Lifecycle de um ADR

```
Proposed ──► Accepted ──► Deprecated
                  │              │
                  └──────────────┴──► Superseded by ADR-NNN
```

| Estado | Significado | Quem pode transitar |
|---|---|---|
| `Proposed` | Rascunho criado, em revisão | Autor |
| `Accepted` | Aprovado e em vigor | Tech Lead ou par sénior |
| `Deprecated` | Já não aplicável (decisão retirada, sem substituto) | Tech Lead |
| `Superseded by ADR-NNN` | Substituído por ADR mais recente | Autor do novo ADR |

**Regra fundamental:** Um ADR nunca é apagado nem editado retroactivamente depois de `Accepted`.
Se a decisão mudar, cria-se um novo ADR que marca o anterior como `Superseded`.

### 4. README.md do directório ADR

O ficheiro `/home/RID/docs/adr/README.md` é um **índice vivo** mantido sempre actualizado:

```markdown
# Architectural Decision Records — RID Platform

| ID | Título | Estado | Data | Ficheiro(s) afectado(s) |
|---|---|---|---|---|
| ADR-001 | sync_to_async tenant isolation | Accepted | ... | api/deps.py |
| ... | ... | ... | ... | ... |

## Como criar um novo ADR

1. Copiar o template de `docs/adr/TEMPLATE.md`
2. Numerar sequencialmente (consultar este README)
3. Estado inicial: `Proposed`
4. PR com revisão de pelo menos 1 par
5. Após merge: atualizar este README
```

---

## Execution Order & Dependencies

### Análise de dependências

```
ADR-001 (sync_to_async)
    └── é pré-requisito conceptual de ADR-003 (arquitectura ASGI)
    └── é pré-requisito operacional de ADR-004 (service layer usa o mesmo padrão)

ADR-002 (users no schema público)
    └── é pré-requisito de ADR-005 (TenantAwareBackend depende desta escolha)

ADR-003 (Django+FastAPI ASGI)
    └── depende de ADR-001 ser compreendido primeiro

ADR-004 (service layer idempotente)
    └── depende de ADR-001 e ADR-002 serem aceites

ADR-005 (TenantAwareBackend)
    └── depende de ADR-002 ser aceite

ADR-006 (porta 5433)
    └── sem dependências — standalone
```

### Ordem de execução recomendada

| Ordem | ADR | Prioridade | Estimativa | Dependências | Gate destravado |
|---|---|---|---|---|---|
| 1º | ADR-001 | P0 | 45 min | Nenhuma | Gate 4 (parcial) |
| 2º | ADR-002 | P0 | 30 min | Nenhuma | Gate 4 (completo) |
| 3º | ADR-003 | P1 | 40 min | ADR-001 aceite | Gate 5 (parcial) |
| 4º | ADR-004 | P1 | 35 min | ADR-001, ADR-002 aceites | Gate 5 (parcial) |
| 5º | ADR-005 | P2 | 30 min | ADR-002 aceite | Gate 5 (completo) |
| 6º | ADR-006 | P3 | 15 min | Nenhuma | Onboarding |

**Estimativa total:** ~3h15min para os 6 ADRs (incluindo revisão cruzada).
**Caminho crítico (P0):** ADR-001 → ADR-002 → ~1h15min → Gate 4 desbloqueado.

### Justificação da ordem

- **ADR-001 primeiro** porque é a decisão técnica mais subtil e de maior risco de regressão.
  A lógica de `thread_sensitive=True` em `api/deps.py:69` é não-óbvia — qualquer "optimização"
  a remove. Precisa de estar documentada antes de qualquer novo endpoint ser criado (Gate 4).

- **ADR-002 segundo** porque qualquer modelo novo criado em Gate 4 precisa saber onde os
  utilizadores vivem. Equivoco aqui quebra migrações.

- **ADR-003 terceiro** porque contextualiza a arquitectura para novos engenheiros, mas não
  bloqueia features imediatas — o routing ASGI em `core/asgi.py` já está estável.

- **ADR-004 quarto** porque o service layer (`tenants/services.py`) ainda está em construção
  (Task 9 do plano de code review). O ADR deve ser escrito quando a implementação estiver
  completa para reflectir o estado real.

- **ADR-005 quinto** porque o `TenantAwareBackend` é estável mas a integração SSO/SAML é
  futuro distante — P2 é correcto.

- **ADR-006 por último** porque é operacional/onboarding, zero risco técnico.

---

## Definition of Done — ADR

Um ADR está **done** quando cumpre **todos** os critérios abaixo:

### Checklist estrutural (verificável por script)

- [ ] Ficheiro existe em `/home/RID/docs/adr/ADR-{NNN}-{slug}.md`
- [ ] Nome do ficheiro segue convenção `ADR-NNN-slug-kebab.md`
- [ ] Contém todas as 8 secções obrigatórias do template MADR
- [ ] Campo `Estado:` é um valor válido do lifecycle
- [ ] Campo `Contexto de código:` aponta para ficheiro(s) existente(s)
- [ ] README.md em `/home/RID/docs/adr/README.md` foi actualizado com a nova entrada

### Checklist de conteúdo (verificável por revisão humana)

- [ ] Secção **Contexto** explica o problema sem mencionar a solução
- [ ] Secção **Decisão** é uma frase afirmativa única e clara
- [ ] **Mínimo 2 alternativas** consideradas (mesmo que óbvias) com motivo de rejeição
- [ ] **Mínimo 1 consequência negativa/trade-off** documentada (sem trade-offs = sinal de ADR incompleto)
- [ ] Secção **Compliance** especifica como auditar a decisão (test, linter, code comment ou PR checklist)
- [ ] Secção **Referências** aponta para `ficheiro:linha` no código actual

### Critério de aprovação

- Revisado por **pelo menos 1 par** (não o autor)
- Estado actualizado para `Accepted` após revisão
- Nenhuma secção contém `TODO` ou `TBD`

---

## Integration with Dev Cycle

### Gate obrigatório: quando criar ADRs

| Situação | Gate obrigatório | Acção |
|---|---|---|
| Decisão afecta isolamento de dados (multi-tenancy) | Gate 0.5 (após implementação, antes de testes) | Criar ADR P0 |
| Decisão afecta autenticação ou autorização | Gate 0.5 | Criar ADR P0 |
| Mudança de arquitectura (novo serviço, nova integração) | Gate 1 (antes de DevOps) | Criar ADR P1 |
| Padrão de código reutilizável estabelecido | Gate 3 (após testes) | Criar ADR P1/P2 |
| Decisão operacional (porta, configuração, Docker) | Gate 1 | Criar ADR P3 |
| Supersede de ADR existente | Qualquer gate | Criar novo ADR + marcar anterior como Superseded |

### Integração com PR checklist

Todo PR que afecte ficheiros em `core/`, `api/deps.py`, `apps/*/models.py`,
`apps/*/services.py`, ou `docker-compose.yml` deve incluir no corpo do PR:

```
## ADR Impact
- [ ] Esta mudança é coberta por ADR existente: ADR-{NNN}
- [ ] Esta mudança requer novo ADR (criar antes de merge): ADR-{NNN} — {título}
- [ ] Esta mudança não requer ADR (motivo: {razão})
```

### Gate 3.5 como gate permanente

A partir deste ciclo, o pipeline de gates inclui **Gate 3.5 — ADR Review**:

```
Gate 3 (testes verdes)
    └── Gate 3.5: verificar se novas decisões arquitecturais foram documentadas
        └── Critério de saída: nenhum ADR em estado Proposed > 48h sem revisão
    └── Gate 4 (feature)
```

O Gate 3.5 é **não-bloqueante para P1/P2/P3** mas **bloqueante para P0**.

### Triagem automática de prioridade

| Critério | Prioridade atribuída |
|---|---|
| Afecta isolamento de tenant (set_tenant, schema, connection) | P0 |
| Afecta auth/authn/authz | P0 |
| Afecta arquitectura de processo (ASGI, workers, async) | P1 |
| Afecta service layer ou padrão de negócio | P1 |
| Afecta integração externa (SSO, Stripe, Langflow) | P2 |
| Afecta ambiente de desenvolvimento/Docker | P3 |

---

## Compliance Metrics

### Métricas de cobertura

| Métrica | Fórmula | Target | Frequência |
|---|---|---|---|
| **ADR Coverage Rate** | `ADRs Accepted / ADRs identificados × 100` | ≥ 100% em P0, ≥ 80% total | Por gate |
| **ADR Freshness** | ADRs com `Accepted` < 30 dias após decisão tomada | 100% | Por sprint |
| **ADR Decay Rate** | ADRs com código que divergiu da decisão documentada | 0% | Por sprint |
| **PR ADR Compliance** | PRs com ADR Impact checklist / total PRs | ≥ 90% | Por semana |

### Como auditar ADR Decay

Para cada ADR `Accepted`, verificar se o ficheiro de referência ainda existe
e se o padrão descrito ainda está presente:

```bash
# ADR-001: verificar thread_sensitive=True em deps.py
grep -n "thread_sensitive=True" /home/RID/backend/api/deps.py

# ADR-002: verificar SHARED_APPS inclui accounts
grep -n "accounts" /home/RID/backend/core/settings.py | grep SHARED

# ADR-003: verificar routing ASGI em asgi.py
grep -n "_API_PREFIX" /home/RID/backend/core/asgi.py

# ADR-006: verificar porta 5433 no docker-compose
grep -n "5433" /home/RID/docker/docker-compose.yml
```

Estes comandos devem ser executados em cada End Stage Assessment.

### Dashboard de compliance (manual — até CI existir)

Manter o `README.md` do directório ADR com coluna `Compliance Check`:

```markdown
| ID | Estado | Último check | Resultado |
|---|---|---|---|
| ADR-001 | Accepted | 2026-04-03 | ✅ grep confirmado |
| ADR-002 | Proposed | — | 🔴 Pendente |
```

---

## Compliance Status

### Score actual (2026-04-03)

| ADR | Código existe | ADR documentado | Estado | Compliance Score |
|---|---|---|---|---|
| ADR-001 | ✅ `api/deps.py:69` | ❌ Falta | — | 0/1 |
| ADR-002 | ✅ `core/settings.py` SHARED_APPS | ❌ Falta | — | 0/1 |
| ADR-003 | ✅ `core/asgi.py` | ❌ Falta | — | 0/1 |
| ADR-004 | ⚠️ `tenants/signals.py` (parcial — services.py pendente) | ❌ Falta | — | 0/1 |
| ADR-005 | ⚠️ `core/auth_backends.py` (Task 8 pendente) | ❌ Falta | — | 0/1 |
| ADR-006 | ✅ `docker-compose.yml:5433` | ❌ Falta | — | 0/1 |

**Score total: 0/6 (0%)**
**Score P0: 0/2 (0%) — CRÍTICO**
**Score P1: 0/2 (0%) — ALTO**

> Nota: "código existe" significa que a decisão foi implementada mas não formalizada.
> Os ADRs ⚠️ têm implementação parcial — o ADR deve ser escrito quando a implementação
> (Tasks 8 e 9 do plano de code review) estiver completa.

---

## Recommendations

### Imediatos (próximas 2h — desbloquear Gate 4)

| # | Acção | Responsável | Prazo | Output |
|---|---|---|---|---|
| R1 | Criar `docs/adr/TEMPLATE.md` com o template MADR deste plano | Engenheiro | Hoje | Ficheiro criado |
| R2 | Criar `docs/adr/README.md` (índice vivo) | Engenheiro | Hoje | Ficheiro criado |
| R3 | Escrever ADR-001 (`sync_to_async` tenant isolation) | Engenheiro sénior | Hoje | Estado: Accepted |
| R4 | Escrever ADR-002 (users no schema público) | Engenheiro sénior | Hoje | Estado: Accepted |

### Curto prazo (Gate 4 em curso — máx 48h)

| # | Acção | Responsável | Prazo | Output |
|---|---|---|---|---|
| R5 | Concluir Tasks 8+9 do code-review-fixes.md | Engenheiro | 1 dia | Código completo |
| R6 | Escrever ADR-003 (arquitectura ASGI híbrida) | Engenheiro sénior | 1 dia | Estado: Accepted |
| R7 | Escrever ADR-004 (service layer idempotente) — após Task 9 | Engenheiro | 1 dia | Estado: Accepted |

### Médio prazo (antes de Gate 5)

| # | Acção | Responsável | Prazo | Output |
|---|---|---|---|---|
| R8 | Escrever ADR-005 (TenantAwareBackend) — após Task 8 | Engenheiro | Gate 5 | Estado: Accepted |
| R9 | Escrever ADR-006 (porta 5433) | Qualquer engenheiro | Gate 5 | Estado: Accepted |
| R10 | Adicionar PR checklist ADR Impact ao template de PR | Tech Lead | Gate 4 | PR template actualizado |
| R11 | Adicionar Gate 3.5 ao ciclo de gates documentado | Tech Lead | Gate 5 | `CONTRIBUTING.md` actualizado |

### Estrutural (sem prazo fixo)

| # | Acção | Responsável | Prazo | Output |
|---|---|---|---|---|
| R12 | Criar script de audit de ADR decay (bash) | Engenheiro | Gate 6 | `scripts/audit-adrs.sh` |
| R13 | Incluir audit de ADRs no End Stage Assessment de cada gate | Tech Lead | Permanente | Processo documentado |

---

## Blockers

### Blocker B1 — ADR-004 e ADR-005 aguardam código

**Descrição:** Os ADRs ADR-004 (service layer) e ADR-005 (TenantAwareBackend) dependem das
Tasks 8 e 9 do plano `2026-04-03-code-review-fixes.md`, que ainda não foram executadas.
Escrever o ADR antes do código estar completo cria risco de divergência imediata.

**Impacto:** ADR-004 e ADR-005 não podem ir para `Accepted` enquanto o código referenciado
não existir.

**Resolução:** Executar Tasks 8 e 9 → verificar código → escrever ADR → Accepted.

**Não bloqueia Gate 4** (apenas Gate 5).

---

### Blocker B2 — Ausência de processo de revisão formalizado

**Descrição:** O projecto ainda não tem um processo de PR review documentado. O critério
"revisado por pelo menos 1 par" no Definition of Done pressupõe este processo.

**Impacto:** Baixo para o estado actual (equipa pequena). Aumenta com escala.

**Resolução:** Criar `CONTRIBUTING.md` com processo de revisão antes de Gate 5 (R11).

---

*Este plano é um documento de governance, não de implementação.
O conteúdo interno de cada ADR é produzido em fase separada.*
