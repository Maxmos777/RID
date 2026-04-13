# Processo de Contribuição — Governance PMO

**Projecto:** RID Platform
**Data:** 2026-04-03
**Estado:** Activo
**Versão:** 1.0
**Fundamento:**
- *PMO Practice Guide* §4.2 — Governance Framework
- *PMBOK 8th Ed.* §2.7 — Project Work Domain
- *Software Extension to PMBOK 5th Ed.* §5 — Configuration Management

---

## Finalidade

Define o processo de contribuição de código e documentação para o RID Platform, com foco em compliance com os ADRs e o gate lifecycle.

**Este documento (PMO)** → governance, critérios, processo formal
**`/home/RID/CONTRIBUTING.md`** → referência de engenharia (comandos, setup, code style)

---

## PR Checklist Obrigatório

Todo PR que altere `core/`, `api/deps.py`, `apps/*/models.py`, `apps/*/services.py`, `docker-compose.yml` ou `pmo/` deve incluir:

### ADR Impact

- [ ] Coberto por ADR existente: **ADR-{NNN}** — *{título}*
- [ ] Requer novo ADR (criar antes de merge): **ADR-{NNN}** — *{título proposto}*
- [ ] Não requer ADR (motivo: _____)

### Gate Impact

- [ ] Mudança compatível com o gate actual
- [ ] Mudança altera entry/exit criteria de um gate → actualizar `pmo/governance/gate-lifecycle.md`

### Scope Impact

- [ ] Dentro do scope do Project Charter
- [ ] Scope creep → aprovação Product Owner + entrada em `pmo/decisions/decision-log.md`

---

## Definition of Done (DoD)

### Feature / Task

- [ ] `pytest` passado + cobertura ≥ 85%
- [ ] `ruff check .` — All checks passed
- [ ] `pytest tests/test_architecture.py` — 15/15 PASS
- [ ] ADR criado se decisão arquitectural nova
- [ ] `pmo/delivery/change-log.md` actualizado na secção `[Unreleased]`
- [ ] Revisão por ≥ 1 par

### ADR

- [ ] Template MADR completo (8 secções, sem `TODO`/`TBD`)
- [ ] Estado final: `Accepted`
- [ ] `docs/adr/README.md` actualizado

### Gate Closure

- [ ] End Stage Assessment em `pmo/performance/gate-reports/gate-{N}-end-stage-assessment.md`
- [ ] RAID log revisto
- [ ] Entry criteria do próximo gate documentadas no Assessment

---

## Gate 3.5 — ADR Compliance Review

**Critério de entrada:** Gate 3 concluído (testes passados, lint limpo).

**Acção:**
```bash
# Correr audit de arquitectura (testes pytest)
cd /home/RID/backend && pytest tests/test_architecture.py -v
# Expected: 15 passed
```

**Critério de saída:**
- ADRs P0 em `Accepted`: **bloqueante**
- ADRs P1/P2/P3: podem prosseguir em paralelo com Gate 4

---

## Triagem de Prioridade ADR

| Critério | Prioridade |
|---|---|
| Afecta isolamento de tenant (set_tenant, schema, connection) | P0 — bloqueia merge |
| Afecta auth / authn / authz | P0 — bloqueia merge |
| Afecta arquitectura de processo (ASGI, workers, async) | P1 — resolver em 48h |
| Afecta service layer ou padrão de negócio reutilizável | P1 — resolver em 48h |
| Afecta integração externa (Stripe, Langflow, SSO) | P2 — antes do gate |
| Afecta ambiente de desenvolvimento / Docker | P3 — pode ir no PR seguinte |

---

## Processo de Revisão

1. Autor abre PR com as três secções do checklist preenchidas
2. Reviewer (≥ 1 par ou Tech Lead) verifica checklist + código + impacto ADR
3. Se "requer novo ADR" está marcado: ADR deve estar em `Accepted` antes do merge
4. Merge apenas após ✅ em todos os itens obrigatórios

---

## Referências

- `pmo/governance/adr-governance-plan.md` — framework ADR completo
- `pmo/uncertainty/raid-log.md` — RAID I1 (origem deste documento)
- `pmo/planning/software-lifecycle-baseline.md` — V&V criteria por gate
- *PMO Practice Guide* §4.2; *PMBOK 8th* §2.7; *Software Extension 5th* §5
