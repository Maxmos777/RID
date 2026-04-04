# ADR-008 — Personalização do Frontend Langflow via Customization Overlay + Custom Docker Image

**Data:** 2026-04-04
**Estado:** Proposed
**Autores:** RID Platform Team
**Revisores:** Tech Lead, Frontend Engineer
**Contexto de código:** `docker-compose.yml`, `langflow-custom/` (a criar), `docs/plans/2026-04-04-langflow-frontend-customization.md`

---

## Contexto

O RID Platform usa a imagem Docker oficial `langflowai/langflow:1.8.3` (ADR-003, ADR-006). A imagem serve o frontend Langflow sem qualquer personalização — branding genérico, feature flags não ajustadas ao produto e sem integração com o contexto de tenant do RID.

No projecto legado (RockItDown), a personalização foi feita copiando os **1.371 ficheiros** do repositório Langflow para dentro do projecto e mantendo um fork embutido. Essa abordagem criou:
- Acoplamento total ao snapshot de uma versão específica
- Ausência de rastreabilidade das mudanças próprias vs. upstream
- Impossibilidade prática de actualizar o Langflow sem reconciliação manual massiva
- Overhead de manutenção desproporcionado para uma equipa pequena

O repositório Langflow disponibiliza um mecanismo oficial de personalização via directório `src/frontend/src/customization/`, que expõe pontos de extensão explícitos (feature flags, constantes, wrappers de componentes, hooks) sem exigir modificação do código-fonte principal.

## Decisão

Mantemos apenas os **ficheiros de personalização próprios** no repositório RID (directório `langflow-custom/customization/`) e construímos uma imagem Docker derivada em build time: clonamos o source do Langflow na tag pinnada, copiamos os nossos overrides por cima do directório `customization/` oficial, fazemos o build do frontend e produzimos `langflowai/langflow:1.8.3-rid` como imagem final. A imagem base continua a ser `langflowai/langflow:1.8.3` para o runtime do backend Langflow.

```
RID repo:
  langflow-custom/
    customization/          ← APENAS o que é nosso
    Dockerfile.langflow     ← build pipeline

Build time:
  git clone langflow@1.8.3 (sparse: src/frontend)
  cp langflow-custom/customization/ → src/frontend/src/customization/
  npm run build
  FROM langflowai/langflow:1.8.3
  COPY dist/ → assets da imagem base

Runtime:
  docker-compose usa langflowai/langflow:1.8.3-rid
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Fork com upstream tracking (branch `rid/custom` no fork do Langflow) | Overhead de manutenção de ~100k ficheiros desproporcionado para a equipa. Upstream move-se rápido; merge conflicts frequentes. Contradiz a estratégia de pinnar versão (ADR-003). |
| Patches versionados (`git format-patch`) sobre sparse checkout | Útil se precisarmos modificar ficheiros fora de `customization/`. Não é o caso actual. Patch hell em upgrades quando os hunks mudam de linha. Reservado como complemento se necessário. |
| Runtime injection via Nginx (`sub_filter` CSS/JS) | Limitado a branding superficial. Não suporta override de comportamento (auth flow, feature flags, hooks). Frágil perante mudanças no HTML gerado pelo Langflow. |
| Cópia completa do source (abordagem legado) | Causa exactamente os problemas que este ADR resolve: 1.371 ficheiros a manter, sem rastreabilidade de mudanças próprias, actualização inviável na prática. |
| Iframe embutido no frontend RID | UX degradada. Não resolve personalização. Cross-origin complexo para contexto de tenant e auth. |

## Consequências Positivas

- O repositório RID contém apenas o que é genuinamente propriedade do produto — dezenas de ficheiros em vez de milhares.
- Rastreabilidade total: qualquer `git diff` no directório `langflow-custom/customization/` mostra exactamente o que diverge do upstream.
- Upgrade do Langflow = alterar a tag em `Dockerfile.langflow` + verificar se os pontos de extensão do `customization/` mudaram + re-build. Processo explícito e controlado.
- Builds reproduzíveis: a imagem `langflowai/langflow:1.8.3-rid` é determinística e versionável em registry.
- Alinhamento com o mecanismo oficial: se o Langflow evoluir o sistema de `customization/`, o nosso overlay beneficia dessa evolução.

## Consequências Negativas / Trade-offs

- **Build time:** A construção da imagem custom demora 5–15 minutos (clone + npm install + build), mas corre apenas quando `langflow-custom/` muda — não em cada ciclo de desenvolvimento. O fluxo normal é: CI detecta mudança → constrói → faz push da imagem para registry; todos os outros devs fazem `docker pull` (~segundos). O dev que altera a customização Langflow paga o custo uma vez; o restante da equipa nunca o sente. Requer registry de imagens (GHCR, ECR ou Docker Hub) — sem registry, cada dev precisaria buildar localmente.
- **Dependência de acesso ao git do Langflow em build time:** Se o repositório upstream estiver indisponível, o build falha. Mitigação: cache da layer de clone no CI ou mirror local da tag.
- **Limite do mecanismo oficial:** Personalizações que exijam modificar ficheiros fora de `customization/` (ex: routing interno, auth flow profundo) não são cobertas pela Opção 1 isolada. Nesses casos, complementar com patches versionados (Opção 2 como adenda).
- **Contrato implícito dos ficheiros overridados:** Qualquer ficheiro do `customization/` que seja substituído pelo overlay deve manter **todas as exportações do upstream** — não apenas as que diferem. O override é um substituto completo do ficheiro. Violação deste contrato causa falha de build (confirmado em IB-001 e IB-002 — ver Apêndice). Mitigação: ao fazer upgrade de versão, fazer diff entre o upstream e o overlay antes de buildar.
- **`outDir` do Vite pode variar entre versões:** O Langflow 1.8.3 outputa para `build/` (não o default `dist/` do Vite). O Stage 2 do Dockerfile deve referenciar o `outDir` correcto (confirmado em IB-003 — ver Apêndice). Mitigação: verificar `vite.config` em cada upgrade de versão.

## Compliance

```bash
# 1. Verificar que o docker-compose usa a imagem rid (não a imagem base directamente)
grep "langflowai/langflow" /home/RID/docker-compose.yml
# Expected: langflowai/langflow:1.8.3-rid  (não :1.8.3 sem sufixo -rid)

# 2. Verificar que não existe cópia do source Langflow no repo
find /home/RID -path "*/langflow-custom" -prune -o \
  -name "App.tsx" -path "*/langflow/*" -print | grep -v "langflow-custom"
# Expected: sem resultados (nenhuma cópia do source fora de langflow-custom/)

# 3. Verificar que langflow-custom/ contém apenas customization/ e Dockerfile.langflow
ls /home/RID/langflow-custom/
# Expected: customization/  Dockerfile.langflow

# 4. Verificar que a tag do Langflow está alinhada entre docker-compose e Dockerfile.langflow
grep -h "1\." /home/RID/docker-compose.yml /home/RID/langflow-custom/Dockerfile.langflow \
  | grep langflow | grep -oP "\d+\.\d+\.\d+" | sort -u
# Expected: uma única versão (sem drift entre ficheiros)
```

## Referências

- `docker-compose.yml` — serviço `langflow` (imagem base actual)
- `langflow-custom/` — directório a criar (ver plano de implementação)
- [Langflow customization/ — source oficial](https://github.com/langflow-ai/langflow/tree/main/src/frontend/src/customization)
- `docs/plans/2026-04-04-langflow-frontend-customization.md` — plano de implementação detalhado (inclui intercorrências IB-001 a IB-003)
- ADR-003 — Arquitectura híbrida Django + FastAPI (contexto de integração Langflow)
- `/home/RockItDown/src/helpers/rock_react/frontend/src/langflow/customization/` — referência de customizações do legado a migrar

---

## Apêndice — Intercorrências de Build (2026-04-04)

Registadas na primeira execução real do pipeline. Servem de referência para upgrades futuros.

### IB-001 — Flags ausentes em `feature-flags.ts`

O upstream v1.8.3 exporta `ENABLE_FETCH_CREDENTIALS`, `LANGFLOW_AGENTIC_EXPERIENCE` e `ENABLE_INSPECTION_PANEL` — flags inexistentes no legado que não foram incluídas no overlay inicial. O build falhou porque `get-fetch-credentials.ts` do upstream importa `ENABLE_FETCH_CREDENTIALS` directamente.

**Regra derivada:** o overlay de `feature-flags.ts` deve exportar **todas** as constantes do upstream. Ao fazer upgrade, comparar com diff:
```bash
diff <(grep "^export const" upstream/feature-flags.ts | sort) \
     <(grep "^export const" langflow-custom/customization/feature-flags.ts | sort)
```

### IB-002 — Exportações base omitidas em `urls.ts`

O override de `urls.ts` definiu apenas `LangflowButtonRedirectTarget` (a customização RID), omitindo `getBaseUrl` e `getHealthCheckUrl` que o resto do upstream importa. Build falhou com export not found.

**Regra derivada:** um override de ficheiro `customization/` substitui o ficheiro integralmente. Manter todas as exportações do upstream mesmo quando não são customizadas.

### IB-003 — `outDir` do Vite é `build/`, não `dist/`

O `vite.config` do Langflow 1.8.3 configura `outDir: "build"`. O Dockerfile inicial referenciava `dist/` (default do Vite), causando falha no Stage 2 com path not found.

**Regra derivada:** verificar `outDir` no `vite.config` em cada upgrade de versão do Langflow.
