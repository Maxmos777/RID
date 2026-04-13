---
feature: rid-langflow-single-entry
gate: 0
date: 2026-04-05
research_mode: integration
agents_dispatched: 4
topology:
  scope: fullstack
  structure: multi-repo
  reference_repo:
    path: /home/RockItDown
    role: padrão de referência (SPA Langflow atrás do Django)
  target_repo:
    path: /home/RID
    role: plataforma a alinhar (bridge + Langflow em contentor)
  api_pattern: bff
---

# Pesquisa Gate 0 — RID alinhado ao padrão RockItDown (Langflow atrás do login)

## Resumo executivo

O **RockItDown** entrega a experiência Langflow como **SPA servida pelo Django** sob `/flows/`, com `LoginRequiredMixin`, e trata o motor Langflow como serviço **interno** (`LANGFLOW_HOST`/`LANGFLOW_PORT`, tipicamente loopback). O **RID** expõe o Langflow como **contentor com `7861:7860` no host** e usa a **bridge** (`/api/v1/langflow/auth/auto-login`) para credenciais — o browser pode falar com o Langflow **sem** passar pelo perímetro de sessão Django. Desenvolver “uma solução como a do RockItDown” no RID implica **mudar topologia de rede e superfície de URL**, não só reforçar o bridge: retirar ou restringir a porta pública, e opcionalmente **proxy/embed** no mesmo domínio que a app, com validação de sessão (nginx `auth_request`, Traefik `forwardAuth`, ou rota Django equivalente).

## Modo de pesquisa

**Integration** — ligar dois sistemas (RID + Langflow) com o mesmo modelo de confiança que o RockItDown já assume (uma “porta de entrada” para a UI sensível).

## Pesquisa no código (Repo Research Analyst)

### RockItDown — padrões a replicar

| Tema | Referência |
|------|------------|
| Rota SPA + include | `src/core/urls_public.py:75` — `path("flows/", include("rocklangflow.urls"))`; espelho em `src/core/urls.py:137-138` |
| API fora do prefixo `/flows/` | `src/core/urls_public.py:145-146` |
| View com login obrigatório | `src/rocklangflow/views/spa.py:15-37` — `LangflowSPA(LoginRequiredMixin, TemplateView)`, `login_url`, `dispatch` com redirect |
| URLs catch-all da SPA | `src/rocklangflow/urls.py:7-10` |
| Config Langflow embutida | `src/core/settings.py:314-335` (`LANGFLOW_HOST`, `LANGFLOW_PORT`, etc.) |
| Estáticos do build React | `src/core/settings.py:286-291` |
| Template wrapper | `src/rocklangflow/views/spa.py:25` → `rocklangflow/langflow/spa_wrapper.html` |
| Narrativa “sem servidor UI separado” | `README.md:58-60`, `82-90` |

### RID — estado actual

| Tema | Referência |
|------|------------|
| Porta Langflow no host | `docker-compose.yml:142-143` — `7861:7860` |
| Runbook (assume URL/base ao Langflow) | `docs/operations/langflow-deployment-and-tenants.md:23-36` |
| Bridge auto-login | `backend/api/routers/langflow_auth.py`; montagem em `backend/api/main.py` (ver imports de router) |
| Cliente HTTP | `backend/api/services/langflow_client.py` — `LANGFLOW_BASE_URL` |
| Frontend | `frontend/apps/rockitdown/src/hooks/useLangflowAuth.ts` |

### Lacuna principal (RID vs RockItDown)

- RID: **UI Langflow = processo próprio publicado** + credenciais via API da app.
- RockItDown: **UI Langflow = resposta HTTP da app após login** + backend Langflow não como “segundo site” para o utilizador final.

### `docs/solutions/`

Não existe **`/home/RockItDown/docs/solutions`** (KB vazia para “soluções anteriores” no sentido Ring). Limitação documentada; conhecimento útil está em README, `docs/operations` no RID, e ADRs em RID (`docs/adr/ADR-008`, `ADR-009`).

## Boas práticas externas (Best Practices Researcher)

| Tema | Fonte |
|------|--------|
| `auth_request` nginx (validar sessão antes do upstream) | https://nginx.org/en/docs/http/ngx_http_auth_request_module.html |
| Traefik `forwardAuth` | https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/forwardauth/ |
| Redes Compose internas / bind mínimo ao host | https://docs.docker.com/reference/compose-file/networks/ , https://docs.docker.com/compose/how-tos/networking/ |
| Langflow atrás de Nginx/SSL, bind local | https://docs.langflow.org/deployment-nginx-ssl |
| Visão geral deploy Langflow | https://docs.langflow.org/deployment-overview |
| Auth / não expor sem proxy | https://docs.langflow.org/configuration-authentication (e página API keys na doc Langflow) |
| Cookies `SameSite` / iframe / subdomínio | https://owasp.org/www-community/SameSite |
| Django atrás de proxy (headers) | https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header |

## Documentação de frameworks (Framework Docs Researcher)

- **RID** (`/home/RID/backend/pyproject.toml`): Django **6.0.3**, FastAPI **0.135.3**, Uvicorn **0.42.0**, django-tenants **3.10.1**, allauth **65.15.1**, Python ≥3.12.
- **Django 6 / async:** usar `request.auser()` em views assíncronas; `LoginRequiredMixin` permanece com `dispatch` síncrono — atenção ao misturar CBV async com mixin clássico ([Async](https://docs.djangoproject.com/en/6.0/topics/async/), [Auth](https://docs.djangoproject.com/en/6.0/topics/auth/default/)).
- **FastAPI:** não partilha sessão Django automaticamente; “mesma sessão” implica validar cookie/sessão (souvent `sync_to_async`) ou **terminar auth no Django/proxy** e passar token curto.
- **Langflow 1.8.x:** CORS via `LANGFLOW_CORS_*`; auth via env documentados; **subpath** costuma exigir ajuste de frontend (`BASENAME`) e/ou reescrita no proxy — ver [environment variables](https://docs.langflow.org/environment-variables) e issues GitHub citadas pelo analista (#8503, #9762).

## Pesquisa de produto / UX (Product Designer, modo ux-research)

- **Problema:** duas entradas (app vs `:7861`) quebram expectativa de **um perímetro** (auditoria, suporte, compliance).
- **Personas:** (1) **Administradora de tenant** — relatórios de acesso alinhados ao IdP; (2) **Construtor de fluxos** — confusão entre URL RID e URL directa ao Langflow.
- **Padrão de mercado:** analytics/BI embutidos servidos **atrás** do SSO da app, não como origem pública paralela.
- **Restrições de desenho:** não promover bookmark em `:7861`; deep links, refresh e **WebSockets** devem funcionar atrás do **mesmo domínio** (ou token de curta duração coerente).
- **Métricas sugeridas:** % sessões Langflow com login RID na mesma janela; tickets “URL/login Langflow”; tentativas de acesso directo a 7861 bloqueadas ou redireccionadas.

## Síntese (para PRD/TRD no RID)

### Padrões a seguir (RockItDown + indústria)

1. **Não publicar** `7861:7860` em ambientes não locais — Langflow só na rede Docker ou `127.0.0.1`, alinhado à doc Langflow de bind local e proxy.
2. **Entrada única da UI:** proxy reverso ou embed que sirva o Langflow sob o **mesmo host** que a app RID, com gate de auth (`auth_request` / `forwardAuth` / view Django com login).
3. **Reutilizar a bridge** RID para tokens/API keys **depois** de garantir que o utilizador não tem caminho “curto” para a UI sem passar pelo gate.
4. **CORS / cookies / WebSockets:** planear explicitamente com `LANGFLOW_CORS_*`, `SameSite`, e headers `X-Forwarded-*` (Django `SECURE_PROXY_SSL_HEADER` já relevante no RockItDown `settings`).

### Restrições identificadas

- **Langflow custom RID** (`langflow-custom/Dockerfile.langflow`, imagem `1.8.3-rid`): qualquer embed/subpath pode exigir **rebuild do frontend** Langflow, não só compose.
- **Django + FastAPI + tenants:** validação de sessão no proxy ou num único “auth check” endpoint evita duplicar lógica async/sync entre stacks.
- **KB `docs/solutions` ausente** no RockItDown — síntese depende de código + ADRs RID.

### Perguntas abertas (PRD)

1. Produção: **apenas** proxy + rede interna, ou também **SPA build** servida pelo Django como no RockItDown (maior paridade, mais trabalho de build/deploy)?
2. WebSockets do Langflow: **mesmo path** no Nginx que HTTP ou serviço separado com mesma política de auth?
3. Critério de aceite: **zero** portas Langflow no host em staging/prod?

---

**Agentes utilizados (ring-pm-team / Gate 0):** `ring:repo-research-analyst`, `ring:best-practices-researcher`, `ring:framework-docs-researcher`, `ring:product-designer` (ux-research).

**Nota multi-repo:** este ficheiro vive no repositório de referência **RockItDown**; o trabalho de implementação pertence ao repositório **RID**. Recomenda-se espelhar um resumo em `RID/docs/pre-dev/` quando a equipa iniciar o PRD.
