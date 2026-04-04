# ADR-010 — Repositório Git na raiz do RID (monorepo) e Ring vendored

**Data:** 2026-04-04  
**Estado:** Accepted  
**Autores:** RID Platform Team  
**Revisores:** Tech Lead, DevOps  
**Contexto de código:** `/.gitignore`, `/.gitattributes`, `/README.md` (secção Git), `/docs/ring-upstream.md`, raiz do repositório `RID/`

---

## Contexto

O projecto RID (`backend/`, `frontend/`, `docs/`, `pmo/`, `langflow-custom/`, `ring/`) existia sem um **único** repositório Git na raiz, ou com repositórios **aninhados** (`backend/.git` sem commits; `ring/.git` apontando para o upstream LerianStudio). Isso impedia `git clone` único, `git status` coerente e integração com CI; `git add` na raiz falhava com *embedded git repository*.

Era necessário definir: uma única árvore versionada na raiz, política de segredos (`.env`), e como incorporar o **Ring** (framework de agentes/skills) sem submodule obrigatório para simplificar o clone inicial.

## Decisão

1. **Monorepo Git na raiz** `RID/`: branch por defeito `main`; `git config --local` para `user.name` / `user.email` (documentado no `README.md` — cada developer substitui o placeholder).

2. **`.gitignore` na raiz** cobre segredos e artefactos gerados: `.env`, `.env.*` (exceto `.env.example`), `__pycache__/`, `.venv/`, `node_modules/`, caches `pytest`/`ruff`, `backend/staticfiles/`, etc.

3. **`.gitattributes`**: `* text=auto eol=lf` (e scripts shell com LF) para consistência entre SO.

4. **Remoção de `.git` aninhado**:
   - `backend/.git` — repositório inicializado mas sem commits; removido para o conteúdo passar a ser rastreado pelo repo raiz.
   - `ring/.git` — removido; o conteúdo de `ring/` é **vendored** (ficheiros normais no monorepo). O upstream oficial fica registado em `docs/ring-upstream.md` (URL https://github.com/LerianStudio/ring.git) para actualizações manuais ou futura política de subtree/submodule.

5. **Não** usar submodule Git para `ring/` nesta fase: prioridade a um único `git clone` e histórico linear no RID; trade-off é perder `git pull` dentro de `ring/` até se adoptar subtree ou submodule num ADR futuro.

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Submodule `ring` | Clone requer `git submodule update --init`; mais passos e falhas frequentes em CI/onboarding. |
| Manter `ring/.git` e ignorar `ring/` no repo raiz | Ring deixaria de ser versionado com o RID; clones incompletos. |
| Só repo em `backend/` | Fragmenta frontend, docs, compose e Langflow custom no mesmo produto. |
| Git LFS para todo o monorepo | Overhead desnecessário para o tamanho actual do tree. |

## Consequências Positivas

- Um comando `git clone` obtém backend, frontend, docs, PMO, Ring e Langflow custom.
- `.env` e caches não entram acidentalmente no histórico (desde que o ignore seja respeitado).
- Documentação explícita do upstream Ring para auditoria e upgrades.

## Consequências Negativas / Trade-offs

- **Actualizar o Ring** exige processo manual (diff/substuição ou futuro ADR para submodule/subtree); não há `git pull` dentro de `vendor/ring`.
- **Histórico do Ring upstream** não está preservado no RID — apenas snapshot de ficheiros.
- Developers devem configurar `user.email` / `user.name` localmente; placeholders no repo não substituem identidade real para push.

## Compliance

```bash
# Repositório na raiz com branch main
test -d /home/RID/.git && git -C /home/RID rev-parse --abbrev-ref HEAD | grep -q main

# Ficheiros de política presentes
test -f /home/RID/.gitignore && test -f /home/RID/.gitattributes

# .env do backend ignorado (se existir)
test -f /home/RID/backend/.env && git -C /home/RID check-ignore -q backend/.env

# ring/ não é submodule (não deve aparecer como 160000 no índice após correcção)
git -C /home/RID ls-files -s ring | head -1 | grep -qv "^160000"
```

Item de **PR checklist**: não adicionar `.env` nem `node_modules/`; não reintroduzir `ring/.git` sem novo ADR.

## Referências

- `README.md` — secção «Git (repositório local)»
- `docs/ring-upstream.md` — URL upstream do Ring
