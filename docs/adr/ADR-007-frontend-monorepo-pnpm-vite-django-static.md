# ADR-007 — Frontend Monorepo (pnpm) + Vite → Django static

**Data:** 2026-04-03  
**Estado:** Proposed  
**Autores:** RID Platform AI Assistant  
**Revisores:** Frontend Engineer, Technical Governance  
**Contexto de código:** `docs/plans/2026-04-03-rid-platform-architecture.md` (Phase 4 Tasks 4.1–4.4), `backend/templates/apps/rockitdown/index.html`, `backend/static/apps/rockitdown/assets/` (destino do build)

---

## Contexto

O RID Platform precisa servir um SPA React a partir do backend Django, para permitir injeção server-side de contexto (tenant schema, URLs de API e CSRF) no HTML inicial. Ao mesmo tempo, a build do SPA deve produzir bundles otimizados e com nomes estáveis para o Django referenciar `index.js` e `index.css` via `{% static %}` sem depender de hashes.

Além disso, a arquitetura prevê múltiplas “apps” frontend no futuro (ex.: RockItDown e outros módulos), o que exige um padrão de repositório que facilite compartilhamento de tipos/config e consistência de tooling (TypeScript, lint e build).

---

## Decisão

Adotamos um **monorepo frontend** usando **pnpm workspaces** e **Vite (React + TypeScript)** para construir o SPA, copiando os artefatos de `dist/assets/` para `backend/static/apps/rockitdown/assets/`, enquanto o **entrypoint** (`index.html`) é servido por **templates Django**.

---

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Servir o `index.html` como arquivo estático gerado pelo Vite (sem template Django) | Perde capacidade de injetar `app_config_json` server-side (tenant + endpoints + CSRF) diretamente no HTML inicial. |
| Sem monorepo (um repo por app frontend) | Dificulta compartilhamento de tipos e padronização de tooling; aumenta custo de manutenção e coordenação. |
| Usar Webpack ao invés de Vite | Rejeitado por aumentar complexidade do setup e reduzir velocidade do ciclo dev/build (objetivo do RID: iterar rápido e com governança simples). |

---

## Consequências Positivas

- Compartilhamento de tipos/config através do pacote `@rid/shared` (ex.: `AppConfig`, `TenantInfo`).
- Bundles com **nomes estáveis** para o Django referenciar `assets/index.js` e `assets/index.css`.
- Injeção server-side do contexto no HTML inicial mantém o SPA desacoplado de múltiplos endpoints “bootstrap”.
- Estrutura escalável para adicionar mais `apps/*` no monorepo sem reinventar tooling.

---

## Consequências Negativas / Trade-offs

- Exige um script de pós-build (`copy-to-django.js`) para copiar somente os assets relevantes do `dist/` do Vite para o diretório `static/` do Django.
- Desenvolvimento local depende de Node + pnpm e do ecossistema Vite/React.

---

## Compliance

Verificações (simples e determinísticas por inspeção de ficheiros):

```bash
# 1) pnpm workspaces root existe
test -f /home/RID/frontend/pnpm-workspace.yaml

# 2) Vite config define nomes estáveis para index.css e index.js
rg 'entryFileNames:\\s*"assets/index\\.js"' /home/RID/frontend/apps/rockitdown/vite.config.ts
rg 'assetFileNames:\\s*"assets/\\[name\\]\\.\\[ext\\]"' /home/RID/frontend/apps/rockitdown/vite.config.ts

# 3) script de copy-to-django existe
test -f /home/RID/frontend/apps/rockitdown/scripts/copy-to-django.js
```

Além disso, o PR checklist deve confirmar que o template Django continua referenciando:
- `static/apps/rockitdown/assets/index.js`
- `static/apps/rockitdown/assets/index.css`

---

## Referências

- `docs/plans/2026-04-03-rid-platform-architecture.md` (Phase 4 Tasks 4.1–4.4)
- `backend/templates/apps/rockitdown/index.html` — entrada e `app-config_json` no HTML

