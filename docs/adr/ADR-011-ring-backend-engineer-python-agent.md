# ADR-011 — Agente Ring `ring:backend-engineer-python` e skill Cursor

**Data:** 2026-04-04  
**Estado:** Accepted  
**Autores:** RID Platform Team  
**Revisores:** Tech Lead, Platform Engineering  
**Contexto de código:** `ring/dev-team/agents/backend-engineer-python.md`, `ring/dev-team/skills/using-dev-team/SKILL.md`, `ring/docs/AGENT_DESIGN.md`, `ring/docs/WORKFLOWS.md`, `.cursor/skills/backend-engineer-python/SKILL.md`

---

## Contexto

O Ring já expunha agentes backend **`ring:backend-engineer-golang`** e **`ring:backend-engineer-typescript`**, com schema de saída, carregamento de standards via WebFetch e integração em `using-dev-team`. O stack do **RID** é **Python** (Django 6, FastAPI, django-tenants, pytest, ruff), sem agente dedicado — levava a despachos incorrectos ou implementação directa sem contrato de saída alinhado ao Ring.

Era necessário um agente especialista Python espelhando a **forma** dos agentes Go/TS (YAML frontmatter, secções obrigatórias, validação pós-implementação), mas com **fonte de standards** adequada ao ecossistema Python do RID (PROJECT_RULES + ADRs, não `golang.md`).

## Decisão

1. **Criar o agente** `ring:backend-engineer-python` em `ring/dev-team/agents/backend-engineer-python.md` com:
   - `name: ring:backend-engineer-python`, `type: specialist`, `version: 1.0.0`
   - **output_schema** alinhado a Go/TS: primeira secção **Standards Verification**; **Post-Implementation Validation** obrigatória com **ruff** e **pytest** (em vez de goimports/golangci-lint ou ESLint/tsc)
   - **input_schema** análogo (task_description, requirements, opcionais)
   - Corpo: âmbito Django/FastAPI, django-tenants, ADR-001/002/003, preferência por testes pytest para compliance (coerente com decisões RID)
   - **Standards**: ler `docs/PROJECT_RULES.md`, `docs/adr/README.md` e `CONTRIBUTING.md` no repositório alvo; não depender de `dev-team/docs/standards/python.md` (inexistente no Ring upstream)

2. **Skill Cursor no projecto RID**: `.cursor/skills/backend-engineer-python/SKILL.md` com frontmatter `name` + `description` (terceira pessoa, triggers), apontando para o agente Ring e comandos de verificação locais.

3. **Registar o agente** em:
   - `ring/dev-team/skills/using-dev-team/SKILL.md` — tabela de especialistas (10 entradas) e texto «Go/TypeScript/Python»
   - `ring/docs/AGENT_DESIGN.md` — lista de agents e tabela «Standards Compliance» com fonte «PROJECT_RULES + docs/adr/»
   - `ring/docs/WORKFLOWS.md` — menção explícita ao novo agente

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Reutilizar só `ring:backend-engineer-typescript` para FastAPI | Perde Django ORM, django-tenants, pytest-django e convenções ADR específicas Python. |
| Agente sem YAML/schema igual ao Go/TS | Inconsistência para orquestradores e validação de resposta. |
| Criar `python.md` no Ring upstream neste PR | Fora do controlo do RID; ADR-011 fixa contrato até existir standard central. |
| Apenas documentação em README sem agente | Não integra Task/dispatch nem secções obrigatórias do Ring. |

## Consequências Positivas

- Despacho explícito para tarefas `backend/**/*.py`, migrações, ASGI, integrações Python.
- Saída previsível (Standards Verification → … → Next Steps) para gates e revisão.
- PMO/dev-cycle podem referenciar o mesmo id de agente que Go/TS.

## Consequências Negativas / Trade-offs

- **Duplicação de “fonte de verdade”**: regras Python dispersas por ADRs + PROJECT_RULES até existir `python.md` no Ring; o agente deve sempre reler ficheiros do repo.
- **Manutenção**: alterações em `using-dev-team` / `AGENT_DESIGN` / `WORKFLOWS` ao adicionar futuros agentes Python-adjacentes.
- **Compliance automatizada**: ADR-011 não adiciona testes em `test_architecture.py` por si só; pode ser alvo de ADR futura ou extensão dos testes de arquitectura.

## Compliance

```bash
# Agente presente
test -f /home/RID/ring/dev-team/agents/backend-engineer-python.md
grep -q "ring:backend-engineer-python" /home/RID/ring/dev-team/agents/backend-engineer-python.md

# Registo em using-dev-team
grep -q "ring:backend-engineer-python" /home/RID/ring/dev-team/skills/using-dev-team/SKILL.md

# Skill Cursor
test -f /home/RID/.cursor/skills/backend-engineer-python/SKILL.md

# Documentação Ring
grep -q "backend-engineer-python" /home/RID/ring/docs/AGENT_DESIGN.md
grep -q "backend-engineer-python" /home/RID/ring/docs/WORKFLOWS.md
```

## Referências

- `ring/dev-team/agents/backend-engineer-golang.md` — modelo de schema e secções
- `ring/dev-team/agents/backend-engineer-typescript.md` — modelo de schema e secções
- `.cursor/skills/backend-engineer-python/SKILL.md` — skill do projecto
