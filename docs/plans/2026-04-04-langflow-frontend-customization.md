# Langflow Frontend Customization — Implementation Plan

**Data:** 2026-04-04
**Status:** Ready for execution
**Decisão arquitectural:** ADR-008
**Contexto:** Substituir a abordagem de fork embutido (legado RockItDown) por um overlay mínimo sobre o mecanismo oficial `customization/` do Langflow, produzindo uma imagem Docker derivada versionada.

---

## Goal

Construir o pipeline `langflow-custom/` que permite personalizar o frontend Langflow de forma sustentável: apenas os ficheiros de override vivem no repo RID; a imagem `langflowai/langflow:1.8.3-rid` é produzida em build time a partir do source oficial pinnado.

---

## Arquitectura alvo

```
/home/RID/
├── langflow-custom/
│   ├── Dockerfile.langflow          ← build pipeline (clone + overlay + build + package)
│   ├── customization/               ← APENAS overrides próprios do RID
│   │   ├── feature-flags.ts
│   │   ├── constants.ts
│   │   ├── config-constants.ts
│   │   ├── custom-App.tsx
│   │   ├── custom-wrapper.tsx
│   │   ├── components/              ← overrides de componentes
│   │   └── hooks/                   ← overrides de hooks
│   └── scripts/
│       └── build-local.sh           ← build manual sem Docker (dev)
└── docker-compose.yml               ← usa langflowai/langflow:1.8.3-rid
```

---

## Fases de execução

### Fase 0 — Auditoria do legado (prerequisito)

Antes de escrever qualquer código novo, auditar o que o legado faz para identificar o que é obrigatório migrar, o que pode ser descartado e o que precisa de re-engenharia.

**Referência:** `/home/RockItDown/src/helpers/rock_react/frontend/src/langflow/customization/`

---

### Fase 1 — Estrutura base e Dockerfile

**Objetivo:** Criar o esqueleto do directório `langflow-custom/` e validar que o build pipeline funciona end-to-end com o `customization/` original do Langflow (zero overrides).

#### Task 1.1 — Criar estrutura de directórios

```bash
mkdir -p /home/RID/langflow-custom/customization/components
mkdir -p /home/RID/langflow-custom/customization/hooks
mkdir -p /home/RID/langflow-custom/scripts
```

**Critério de done:** directórios existem; `langflow-custom/` está no `.gitignore` do backend mas não do repo raiz.

---

#### Task 1.2 — Escrever `Dockerfile.langflow`

Ficheiro: `langflow-custom/Dockerfile.langflow`

```dockerfile
# syntax=docker/dockerfile:1.4

# ─── Stage 1: build do frontend customizado ───────────────────────────────────
FROM node:20-alpine AS frontend-builder

ARG LANGFLOW_VERSION=1.8.3
WORKDIR /build

# Instalar git para sparse checkout
RUN apk add --no-cache git

# Sparse checkout — apenas src/frontend (evita clonar 100k ficheiros)
RUN git clone \
    --filter=blob:none \
    --no-checkout \
    --depth=1 \
    --branch v${LANGFLOW_VERSION} \
    https://github.com/langflow-ai/langflow.git . \
  && git sparse-checkout init --cone \
  && git sparse-checkout set src/frontend \
  && git checkout

WORKDIR /build/src/frontend

# Instalar dependências
RUN npm ci --prefer-offline

# Copiar overrides do RID por cima do customization/ oficial
COPY customization/ src/customization/

# Build
RUN npm run build

# ─── Stage 2: imagem final = langflow base + frontend customizado ──────────────
FROM langflowai/langflow:1.8.3

# Substituir os assets do frontend pela versão customizada
# O frontend buildado fica em /usr/local/lib/python*/dist-packages/langflow/frontend/
# ou equivalente — ajustar o destino conforme inspecção da imagem base
COPY --from=frontend-builder /build/src/frontend/dist/ /app/langflow/frontend/

LABEL org.opencontainers.image.version="1.8.3-rid"
LABEL org.opencontainers.image.description="Langflow 1.8.3 with RID Platform customizations"
```

**Nota:** O path de destino no Stage 2 (`/app/langflow/frontend/`) precisa de ser verificado inspeccionando a imagem base. Ver Task 1.3.

**Critério de done:** Dockerfile existe e passa `docker buildx build --check`.

---

#### Task 1.3 — Inspecionar imagem base para confirmar path dos assets

```bash
# Localizar onde a imagem base serve os assets do frontend
docker run --rm --entrypoint="" langflowai/langflow:1.8.3 \
  find / -name "index.html" -path "*/frontend/*" 2>/dev/null

# Alternativa: inspecionar com shell
docker run --rm -it langflowai/langflow:1.8.3 sh
```

**Output esperado:** path absoluto para os assets do frontend dentro da imagem (ex: `/usr/local/lib/python3.12/site-packages/langflow/frontend/`).

**Critério de done:** `Dockerfile.langflow` Stage 2 usa o path correcto confirmado.

---

#### Task 1.4 — Validar build end-to-end (zero overrides)

```bash
cd /home/RID && docker compose build langflow
docker run --rm -d -p 7860:7860 -e LANGFLOW_SUPERUSER=admin \
  -e LANGFLOW_SUPERUSER_PASSWORD=adminpassword langflowai/langflow:1.8.3-rid
curl -sf http://localhost:7860/health_check
```

**Critério de done:** imagem constrói sem erros; `/health_check` retorna `{"status":"ok","chat":"ok","db":"ok"}`.

> **Intercorrências registadas em 2026-04-04** (ver secção abaixo)

---

### Fase 2 — Migração selectiva do legado

**Objetivo:** Auditar `customization/` do legado e migrar apenas o que é relevante para o RID. Não copiar cegamente — re-avaliar cada override.

#### Task 2.1 — Auditoria e classificação dos overrides do legado

Para cada ficheiro em `/home/RockItDown/src/helpers/rock_react/frontend/src/langflow/customization/`:

| Classificação | Acção |
|---|---|
| **Obrigatório** — afecta auth, tenant context, branding core | Migrar para `langflow-custom/customization/` |
| **Útil** — melhora UX mas não é bloqueante | Migrar se custo baixo |
| **Dispensável** — feature flag de funcionalidade não usada | Descartar |
| **Re-engenharia necessária** — lógica acoplada ao legado | Reescrever limpo |

**Ficheiros prioritários a avaliar:**

| Ficheiro legado | Tipo | Acção esperada |
|---|---|---|
| `feature-flags.ts` | Feature toggles | Migrar — rever cada flag com lógica RID |
| `constants.ts` | Shortcuts, CSS classes | Migrar selectivamente |
| `config-constants.ts` | `PROXY_TARGET`, `API_ROUTES` | Migrar — ajustar endpoints para RID |
| `custom-App.tsx` | Wrapper App | Migrar — simplificar se não faz nada útil |
| `custom-wrapper.tsx` | Children wrapper | Migrar — verificar se é necessário |
| `hooks/use-custom-post-auth.ts` | Auth hook | **Re-engenharia** — integrar com TenantAwareBackend (ADR-005) |
| `hooks/use-custom-api-headers.ts` | API headers | Migrar — adicionar tenant header se necessário |
| `components/custom-header.tsx` | Header | Migrar com branding RID |
| `components/custom-loading-page.tsx` | Loading | Migrar com branding RID |
| `components/custom-DashboardWrapperPage.tsx` | Dashboard wrapper | Avaliar — pode ser dispensável |

**Critério de done:** tabela de classificação preenchida e revista pelo Tech Lead antes de qualquer migração.

---

#### Task 2.2 — Migrar `feature-flags.ts`

Criar `langflow-custom/customization/feature-flags.ts` com as flags relevantes para o RID, documentando o motivo de cada escolha.

```typescript
// langflow-custom/customization/feature-flags.ts
// Overrides das feature flags do Langflow para o RID Platform
// Referência upstream: src/frontend/src/customization/feature-flags.ts@1.8.3

export const ENABLE_DARK_MODE = true;
export const ENABLE_API = true;
export const ENABLE_LANGFLOW_STORE = false;   // desactivado: não usar marketplace público
// ... (completar após Task 2.1)
```

**Critério de done:** ficheiro existe; cada flag tem comentário com motivo da decisão.

---

#### Task 2.3 — Migrar `config-constants.ts`

Ajustar `PROXY_TARGET` e `API_ROUTES` para apontar para a infra RID:

```typescript
// langflow-custom/customization/config-constants.ts
export const PROXY_TARGET = "http://rid-langflow:7860";  // nome do serviço Docker
export const API_ROUTES = ["^/api/v1/", "^/api/v2/", "/health"];
// ...
```

**Critério de done:** build com este override não quebra o proxy Langflow → backend RID.

---

#### Task 2.4 — Migrar / reescrever hooks de auth

O hook `use-custom-post-auth.ts` do legado tem lógica de auth acoplada ao RockItDown. Reescrever para integrar com `TenantAwareBackend` do RID (ADR-005): após login Langflow, propagar o contexto de tenant via header ou cookie.

**Critério de done:** hook migrado; teste manual de login multi-tenant funciona.

---

#### Task 2.5 — Migrar overrides de branding (header, loading)

Componentes de branding simples: substituir logos/cores do Langflow por identidade RID.

**Critério de done:** imagem buildada mostra branding RID no header e loading screen.

---

### Fase 3 — Integração com docker-compose

#### Task 3.1 — Adicionar serviço de build ao docker-compose

Actualizar `docker-compose.yml` para usar a imagem customizada:

```yaml
langflow:
  image: langflowai/langflow:1.8.3-rid   # imagem customizada (ADR-008)
  build:
    context: ./langflow-custom
    dockerfile: Dockerfile.langflow
  container_name: rid-langflow
  # ... resto igual
```

Com `build:` configurado, `docker compose build langflow` reconstrói a imagem customizada.

**Critério de done:** `docker compose up langflow` usa a imagem customizada sem erros.

---

#### Task 3.2 — Script de build local (dev)

Criar `langflow-custom/scripts/build-local.sh` para devs que querem iterar sem Docker:

```bash
#!/usr/bin/env bash
# Build local do frontend customizado (sem Docker)
# Requer: node 20+, git
set -euo pipefail

LANGFLOW_VERSION="${1:-1.8.3}"
WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT

echo "→ Clonando Langflow v${LANGFLOW_VERSION} (sparse)..."
git clone --filter=blob:none --no-checkout --depth=1 \
  --branch "v${LANGFLOW_VERSION}" \
  https://github.com/langflow-ai/langflow.git "$WORK_DIR"
cd "$WORK_DIR"
git sparse-checkout init --cone
git sparse-checkout set src/frontend
git checkout

cd src/frontend
echo "→ Instalando dependências..."
npm ci

echo "→ Copiando overrides RID..."
cp -r "$(dirname "$0")/../customization/" src/customization/

echo "→ Build..."
npm run build

echo "→ Output: $WORK_DIR/src/frontend/dist/"
```

**Critério de done:** script existe, é executável, e produz `dist/` funcional.

---

### Fase 4 — Testes e compliance

#### Task 4.1 — Smoke test da imagem customizada

```bash
# Verificar que a imagem sobe e serve o frontend
docker run --rm -d -p 7860:7860 --name test-langflow langflowai/langflow:1.8.3-rid
sleep 10
curl -f http://localhost:7860/ | grep -i "langflow\|rid"
docker stop test-langflow
```

**Critério de done:** HTTP 200 com HTML que inclui referências ao branding RID.

---

#### Task 4.2 — Adicionar verificações de compliance ao `test_architecture.py`

```python
# backend/tests/test_architecture.py — adicionar:

def test_adr_008_langflow_uses_custom_image():
    """ADR-008: docker-compose deve usar imagem rid, não a base."""
    compose = Path("../docker-compose.yml").read_text()
    assert "1.8.3-rid" in compose, (
        "ADR-008: langflow service deve usar langflowai/langflow:1.8.3-rid "
        "(custom image). Ver docs/adr/ADR-008-langflow-frontend-customization-overlay.md"
    )
    assert "image: langflowai/langflow:1.8.3\n" not in compose, (
        "ADR-008: imagem base sem sufixo -rid não deve ser usada directamente."
    )

def test_adr_008_no_langflow_source_copy():
    """ADR-008: não deve existir cópia do source Langflow fora de langflow-custom/."""
    # Verificar que não existe App.tsx do Langflow fora do directório permitido
    forbidden = list(Path("..").glob("**/langflow/App.tsx"))
    allowed_prefix = Path("../langflow-custom")
    violations = [p for p in forbidden if not str(p).startswith(str(allowed_prefix))]
    assert not violations, (
        f"ADR-008: source Langflow copiado fora de langflow-custom/: {violations}"
    )
```

**Critério de done:** testes existem, passam com setup correcto, falham com setup errado.

---

#### Task 4.3 — ADR-008 → Accepted

Após todas as tasks completadas e revistas pelo Tech Lead:
1. Actualizar `ADR-008` de `Proposed` para `Accepted`
2. Actualizar `docs/adr/README.md` com novo estado
3. Actualizar `pmo/decisions/decision-log.md` com ADR-008

---

## Definition of Done (global)

- [ ] `langflow-custom/` existe com estrutura correcta
- [ ] `docker compose build langflow` constrói `langflowai/langflow:1.8.3-rid` sem erros
- [ ] `docker compose up langflow` sobe com branding RID visível
- [ ] Nenhum ficheiro do source Langflow copiado fora de `langflow-custom/`
- [ ] `pytest tests/test_architecture.py` inclui e passa os 2 novos testes ADR-008
- [ ] `feature-flags.ts` migrado com comentários de decisão
- [ ] `config-constants.ts` migrado com endpoints RID
- [ ] Hook de auth integrado com `TenantAwareBackend` (ADR-005)
- [ ] ADR-008 em estado `Accepted`
- [ ] `docs/adr/README.md` actualizado
- [ ] `pmo/decisions/decision-log.md` actualizado

---

## Intercorrências de Build (2026-04-04)

Registadas durante a primeira execução real do pipeline. Cada item é um contrato implícito do upstream que o legado não expunha.

---

### IB-001 — `feature-flags.ts`: flags ausentes no overlay

**Sintoma:** Build falhou com `"ENABLE_FETCH_CREDENTIALS" is not exported by "src/customization/feature-flags.ts"`.

**Causa:** O upstream v1.8.3 adicionou 3 flags que não existiam no legado nem foram incluídas no overlay inicial:
- `ENABLE_FETCH_CREDENTIALS = false`
- `LANGFLOW_AGENTIC_EXPERIENCE = false`
- `ENABLE_INSPECTION_PANEL = true`

**Resolução:** Adicionadas ao `langflow-custom/customization/feature-flags.ts` com comentários de decisão.

**Lição:** O overlay de `feature-flags.ts` deve exportar **todas** as flags do upstream — não apenas as que diferem. O upstream pode adicionar novas flags em qualquer release; o contrato é o ficheiro completo, não um subconjunto.

**Verificação pós-upgrade:** ao actualizar a versão do Langflow, comparar o `feature-flags.ts` upstream com o nosso overlay:
```bash
# diff entre upstream e overlay (requer clone local ou extracção da imagem)
diff <(grep "^export" upstream/feature-flags.ts | sort) \
     <(grep "^export" langflow-custom/customization/feature-flags.ts | sort)
# Expected: apenas diferenças intencionais (ex: ENABLE_KNOWLEDGE_BASES, ENABLE_LANGFLOW_STORE)
```

---

### IB-002 — `urls.ts`: funções base omitidas no override

**Sintoma:** Build falhou com `"getBaseUrl" is not exported by "src/customization/utils/urls.ts"`.

**Causa:** O upstream importa `getBaseUrl` e `getHealthCheckUrl` de `urls.ts`. O nosso override apenas redefiniu `LangflowButtonRedirectTarget` (a única customização RID), omitindo as funções base.

**Resolução:** `urls.ts` passou a exportar as 3 funções: `getBaseUrl`, `getHealthCheckUrl` (idênticas ao upstream), e `LangflowButtonRedirectTarget` (customizada para `docs.ridplatform.com`).

**Lição:** Qualquer ficheiro do `customization/` que seja overridado deve manter **todas as exportações do upstream**, mesmo as que não são customizadas. O override é um substituto completo do ficheiro, não um patch parcial.

---

### IB-003 — Output Vite em `build/` não `dist/`

**Sintoma:** Stage 2 do Dockerfile falhou com `"/build/src/frontend/dist": not found`.

**Causa:** O `vite.config` do Langflow 1.8.3 configura `outDir: "build"` (não o default `dist` do Vite). O Dockerfile inicial usava `dist/`.

**Resolução:** Dockerfile corrigido para `COPY --from=frontend-builder /build/src/frontend/build/ ...`.

**Verificação pós-upgrade:** ao actualizar versão, confirmar o `outDir` do vite.config:
```bash
docker run --rm node:20-alpine sh -c "
  git clone --filter=blob:none --no-checkout --depth=1 --branch v{VERSION} \
    https://github.com/langflow-ai/langflow.git /tmp/lf 2>/dev/null &&
  cd /tmp/lf && git sparse-checkout init --cone &&
  git sparse-checkout set src/frontend && git checkout -q &&
  grep 'outDir' src/frontend/vite.config*
"
```

---

## Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Path dos assets na imagem base diferente do esperado | Média | Alto | Task 1.3 faz inspecção antes do build |
| Contrato de `customization/` mudou entre versões | Baixa (1.8.3 pinnado) | Médio | Verificar em cada bump de versão |
| Build time lento em CI | Alta | Baixo | Cache da layer `npm ci` no CI |
| Hooks de auth do legado têm lógica não documentada | Média | Médio | Task 2.1 faz auditoria explícita antes de migrar |

---

## Referências

- ADR-008: `docs/adr/ADR-008-langflow-frontend-customization-overlay.md`
- Legado: `/home/RockItDown/src/helpers/rock_react/frontend/src/langflow/customization/`
- [Langflow customization/ oficial](https://github.com/langflow-ai/langflow/tree/main/src/frontend/src/customization)
- ADR-003 — Arquitectura ASGI (contexto de integração Langflow)
- ADR-005 — TenantAwareBackend (contexto do hook de auth)
