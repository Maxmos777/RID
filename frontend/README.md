# Frontend — RID Platform

Monorepo frontend (Phase 4) usando `pnpm` + `Vite`/`React`.

## Prerequisitos

- Node.js 20+
- `pnpm`

## Instalar dependências

```bash
cd /home/RID/frontend
pnpm install
```

## Apps disponíveis

- `@rid/rockitdown` (SPA RockItDown) em `apps/rockitdown/`

## Build do RockItDown

O build copia `dist/assets/*` para os assets do Django em:
`/home/RID/backend/static/apps/rockitdown/assets/`

```bash
cd /home/RID/frontend
pnpm --filter @rid/rockitdown build
```

