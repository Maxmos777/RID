---
feature: rid-langflow-single-entry
gate: 6
date: 2026-04-06
status: draft
standards_loaded: [devops.md, frontend.md]
---

# Dependency Map — rid-langflow-single-entry

> Referência arquitectural: [TRD Gate 3](./gate-3-trd.md) — decisões DD-001 a DD-005, Componentes 1–5, ADR-012.
>
> Este documento regista **apenas o que este feature adiciona ou altera**. O stack existente
> (Python 3.12, Django 6.0.3, FastAPI 0.135.3, React 18, Langflow 1.8.3-rid, etc.) não é
> re-documentado aqui.

---

## 1. Resumo de dependências novas

| Tipo | Componente | Versão | Nova dependência? | Novas dependências transitivas? |
|------|-----------|--------|:-----------------:|:-------------------------------:|
| Infra — Docker | Traefik | v3.3.6 | Sim | Não (container isolado) |
| Backend — Django | Auth Check Endpoint | — | Não (usa middleware existente) | Não |
| Backend — Django | Error Page Template | — | Não (template Django nativo) | Não |
| Backend — Django | Django settings (proxy headers) | — | Não (variáveis de ambiente) | Não |
| Frontend — React | Session Expiry Overlay | — | Não (React 18 nativo) | Não |
| Config — docker-compose | `LANGFLOW_BASE_URL` hostname interno | — | Não (alteração de valor) | Não |
| Config — docker-compose | Remoção porta `7861:7860` | — | Não (remoção de config) | Não |

**Conclusão:** a única nova dependência de software introduzida por este feature é o **container Traefik v3.3.6**.
Todos os outros componentes reutilizam o stack existente sem adicionar pacotes Python, npm ou imagens Docker.

---

## 2. Traefik (única dependência de infraestrutura nova)

### 2.1 Identificação

| Atributo | Valor |
|----------|-------|
| Nome | Traefik Proxy |
| Versão exacta | **v3.3.6** |
| Imagem Docker | `traefik:v3.3.6` |
| Licença | MIT |
| Repositório | https://github.com/traefik/traefik |
| Docker Hub | https://hub.docker.com/_/traefik |

### 2.2 Justificação da versão

`v3.3.6` é a versão mais recente da série `v3.3.x` e inclui os patches de segurança
CVE-2025-32431, CVE-2025-22868 e CVE-2025-22871 (ver secção 2.5).
A série v3.x é a linha estável actual; v2.x entrou em EOL.

### 2.3 Configuração necessária

**Command flags do container (sem ficheiro de configuração externo — alinhado ao TRD Componente 1):**

```yaml
command:
  - "--providers.docker=true"
  - "--providers.docker.exposedByDefault=false"
  - "--providers.docker.network=rid-network"
  - "--entrypoints.web.address=:80"
  - "--entrypoints.websecure.address=:443"
  - "--log.level=INFO"
  - "--accesslog=true"
```

**Nota:** toda a configuração de routing e middleware é feita via labels Docker nos serviços,
sem ficheiros `traefik.yml` ou `traefik.toml` externos. Esta abordagem mantém a configuração
versionada no `docker-compose.yml` (requisito TRD Componente 1).

### 2.4 Middleware forwardAuth

Definição do middleware no serviço `traefik` (ou via label em qualquer serviço da rede):

```yaml
labels:
  # Middleware forwardAuth — definição global
  - "traefik.http.middlewares.rid-auth.forwardauth.address=http://backend:8000/internal/auth-check/"
  - "traefik.http.middlewares.rid-auth.forwardauth.trustForwardHeader=true"
  - "traefik.http.middlewares.rid-auth.forwardauth.authResponseHeaders=X-Auth-User,X-Auth-Tenant"
```

| Parâmetro | Valor | Justificação |
|-----------|-------|-------------|
| `address` | `http://backend:8000/internal/auth-check/` | Hostname interno do container Django na rede `rid-network` |
| `trustForwardHeader` | `true` | Necessário para o `TenantMainMiddleware` resolver o tenant via `X-Forwarded-Host` (TRD §7.4) |
| `authResponseHeaders` | `X-Auth-User,X-Auth-Tenant` | Headers injectados no request encaminhado ao Langflow após autorização |

### 2.5 Labels no serviço `langflow` (docker-compose)

```yaml
labels:
  - "traefik.enable=true"
  # Router: captura todo o tráfego /flows/ e sub-paths (incluindo WebSocket)
  - "traefik.http.routers.langflow.rule=PathPrefix(`/flows`)"
  - "traefik.http.routers.langflow.entrypoints=websecure"
  - "traefik.http.routers.langflow.tls=true"
  # Middleware de autenticação obrigatório
  - "traefik.http.routers.langflow.middlewares=rid-auth@docker"
  # Serviço interno — porta interna do container Langflow
  - "traefik.http.services.langflow.loadbalancer.server.port=7860"
  # WebSocket: passar headers Upgrade e Connection (TRD Componente 1)
  - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Connection=keep-alive, Upgrade"
  - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Upgrade=websocket"
  - "traefik.http.routers.langflow.middlewares=rid-auth@docker,langflow-ws@docker"
```

### 2.6 Labels no serviço `backend` (exposição interna do Auth Check Endpoint)

O endpoint `/internal/auth-check/` é acessível ao Traefik via rede interna (`http://backend:8000`).
O backend **não precisa de label Traefik** para este sub-request: o forwardAuth chama directamente
o hostname Docker interno. Não é necessário expor o backend ao Traefik publicamente para este efeito.

Para expor o backend à internet via Traefik (dashboard, API), adicionar:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.backend.rule=Host(`app.rid.example.com`) && !PathPrefix(`/flows`)"
  - "traefik.http.routers.backend.entrypoints=websecure"
  - "traefik.http.routers.backend.tls=true"
  - "traefik.http.services.backend.loadbalancer.server.port=8000"
```

### 2.7 CVE Check — Traefik v3.3.6

| CVE | Severidade | Versões afectadas | Estado em v3.3.6 |
|-----|-----------|-------------------|:----------------:|
| CVE-2025-32431 | High | < v3.3.6 | **Corrigido** |
| CVE-2025-22868 | High | < v3.3.6 | **Corrigido** |
| CVE-2025-22871 | Moderate | < v3.3.6 | **Corrigido** |
| CVE-2026-33186 | High | A verificar | Verificar após release notes de v3.3.7+ |
| GHSA-wvvq-wgcr-9q48 (mTLS bypass) | High | A verificar | Monitorizar changelog |
| GHSA-4hjq-9h5c-252j (HTTP/2 panic) | High | A verificar | Monitorizar changelog |

**Resultado:** `v3.3.6` é a versão mais recente da série v3.3.x com os patches disponíveis à data deste
documento (2026-04-06). Nenhum CVE crítico (CVSS >= 9.0) confirmado nesta versão.
Os advisories de Mar 2026 (CVE-2026-33186, GHSA-wvvq) devem ser monitorizados — verificar se há
`v3.3.7` disponível antes do deploy em produção.

**Acção antes do deploy:** executar `docker scout cves traefik:v3.3.6` ou equivalente no pipeline CI.

### 2.8 Alternativas avaliadas

| Alternativa | Motivo de rejeição |
|-------------|-------------------|
| **nginx** (container) | Requer ficheiro de configuração externo (`nginx.conf`) para implementar auth_request; aumenta superfície de configuração e quebra o requisito de "sem ficheiros de config externos" do TRD. O módulo `ngx_http_auth_request_module` não está disponível na imagem oficial sem compilação custom. |
| **Caddy** | Menos maduro para o padrão forwardAuth em Docker Compose; a directiva `forward_auth` existe mas a documentação de casos de uso multi-tenant com cookie passthrough é escassa; menor adopção em contextos Django multi-tenant. |
| **HAProxy** | Configuração via ficheiro externo obrigatória; sem suporte nativo a labels Docker para configuração dinâmica; overhead operacional mais elevado. |

---

## 3. Alterações de configuração Django (sem novas dependências)

Todas as alterações são variáveis de ambiente ou settings Django — sem novos pacotes Python.

### 3.1 Settings a adicionar/actualizar

| Setting | Valor | Ambiente | Justificação |
|---------|-------|----------|-------------|
| `SECURE_PROXY_SSL_HEADER` | `('HTTP_X_FORWARDED_PROTO', 'https')` | Todos | Django reconhece HTTPS quando atrás de proxy (Traefik injeta este header) |
| `USE_X_FORWARDED_HOST` | `True` | Todos | `TenantMainMiddleware` usa `X-Forwarded-Host` para resolver tenant (TRD §7.4) |
| `SESSION_COOKIE_SECURE` | `True` | Produção/Staging | Cookie de sessão só transmitido via HTTPS — obrigatório com Traefik TLS |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` | Todos | Protecção CSRF sem quebrar fluxos de redirect normais |
| `CSRF_COOKIE_SECURE` | `True` | Produção/Staging | Cookie CSRF só via HTTPS |
| `ALLOWED_HOSTS` | Adicionar domínio de produção + `backend` | Todos | `backend` é necessário para sub-requests internos do forwardAuth; domínio de produção para requests do browser |

### 3.2 Variáveis de ambiente associadas

```dotenv
# .env (produção/staging)
DJANGO_ALLOWED_HOSTS=app.rid.example.com,backend
DJANGO_SECURE_PROXY_SSL_HEADER=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
```

> Seguindo o standard devops.md: variáveis de ambiente via `.env` (nunca inline no docker-compose).
> `.env.example` deve ser actualizado com estas variáveis documentadas.

### 3.3 Endpoint novo: `/internal/auth-check/`

- Sem novas dependências Python.
- Usa `django-tenants` (já existente) para leitura do tenant activo.
- Usa o sistema de sessão nativo do Django (já existente via `redis`).
- Regista evento de auditoria via fire-and-forget async (sistema de auditoria existente).
- Performance target: p95 < 20ms (TRD §8).

---

## 4. Alterações de configuração Langflow (sem novas dependências)

### 4.1 Variável `LANGFLOW_BASE_URL`

| Antes | Depois | Motivo |
|-------|--------|--------|
| `http://localhost:7861` | `http://langflow:7860` | O Langflow comunica com ele próprio via rede interna de containers; a porta pública `7861` é removida |

Esta variável é usada pelo Langflow para gerar URLs de callback e recursos internos. Com a porta
pública removida, o valor deve apontar para o hostname interno (`langflow`) na porta nativa (`7860`).

### 4.2 Variável `LANGFLOW_CORS_ORIGINS`

| Antes | Depois |
|-------|--------|
| Incluía `http://localhost:7861` ou similar | Substituir por `https://app.rid.example.com` (domínio da plataforma, sem porta `7861`) |

O browser acede ao Langflow exclusivamente via Traefik no domínio da plataforma — nunca directamente
na porta `7861`.

### 4.3 Remoção da porta pública do serviço `langflow`

```yaml
# ANTES (remover em staging/produção):
ports:
  - "7861:7860"

# DEPOIS: porta removida — Langflow acessível apenas via Traefik na rede interna
# (sem secção ports no serviço langflow)
```

> O serviço `langflow` permanece na rede `rid-network`. O Traefik comunica com ele via
> `http://langflow:7860` internamente, sem exposição ao host.

### 4.4 Variável `LANGFLOW_BASE_URL` no backend Django

O backend Django referencia o Langflow (bridge de auto-login, ADR-009) via:

```dotenv
# .env
LANGFLOW_BASE_URL=http://langflow:7860
```

Valor anterior `http://localhost:7861` deixa de funcionar após remoção da porta pública.

---

## 5. Heartbeat no frontend (sem novas dependências npm)

### 5.1 Implementação

O Session Expiry Overlay (TRD Componente 3, DD-001) é implementado com APIs nativas do React 18
e do browser — sem bibliotecas externas.

| Aspecto | Detalhe |
|---------|---------|
| Mecanismo | `useEffect` + `setInterval` nativo (Web API) |
| Endpoint | `GET /internal/auth-check/` — acessível ao browser via Traefik (mesmo domínio) |
| Intervalo | **120 segundos** (2 minutos) — alinhado ao TRD Componente 3 |
| Cancelamento | `clearInterval` no cleanup do `useEffect` (evita memory leaks) |
| Trigger de overlay | Resposta HTTP `401` do endpoint |
| Acessibilidade | `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"`, navegação por teclado (Tab, Enter, Escape) — WCAG 2.1 AA (DD-005) |
| Estilo | Inline styles ou CSS plano — sem biblioteca de componentes (DD-004) |
| CTA | "Entrar novamente" → redirect para `/login/?next=/flows/` |

### 5.2 Padrão de implementação

```typescript
// useSessionHeartbeat.ts — hook extraído (frontend standard: hooks > 20 linhas em ficheiro separado)
useEffect(() => {
  const intervalId = setInterval(async () => {
    try {
      const response = await fetch('/internal/auth-check/', {
        credentials: 'same-origin',
      });
      if (response.status === 401) {
        onSessionExpired(); // activa o overlay
      }
    } catch {
      // Falha de rede silenciosa — não activar overlay por erro transitório
    }
  }, 120_000); // 120 segundos

  return () => clearInterval(intervalId); // cleanup obrigatório
}, [onSessionExpired]);
```

> Nota: `credentials: 'same-origin'` garante que o cookie de sessão é enviado no heartbeat.
> O request é feito ao mesmo domínio (via Traefik) — sem CORS necessário.

### 5.3 Alinhamento com standards frontend

| Standard (frontend.md) | Aplicação neste componente |
|------------------------|---------------------------|
| Hook extraído em ficheiro separado (> 20 linhas) | `useSessionHeartbeat.ts` separado do componente |
| `ErrorBoundary` e gestão de erros | Erros de rede silenciosos; overlay apenas em 401 confirmado |
| WCAG 2.1 AA | `role="alertdialog"`, `aria-modal`, `aria-live`, navegação teclado |
| Sem `useEffect` para data fetching (standard proíbe) | Excepção justificada: heartbeat periódico não é data fetching; é polling de estado de sessão. Não existe abstracção TanStack Query adequada para este padrão de polling de infraestrutura. |

---

## 6. Matriz de compatibilidade

| Componente | Versão | Compatível com | Testado em |
|-----------|--------|----------------|------------|
| Traefik | v3.3.6 | Docker Compose v2.x, rede bridge | Docker Engine 27.x (Linux) |
| Traefik forwardAuth | v3.3.6 | Django 6.0.3 (session middleware) | Python 3.12 / django-tenants 3.10.1 |
| Traefik → Langflow proxy | v3.3.6 | Langflow 1.8.3-rid (HTTP + WebSocket) | langflowai/langflow:1.8.3-rid |
| Django proxy headers | Django 6.0.3 | `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST` | Django 6.0.3 (built-in) |
| `SESSION_COOKIE_SECURE` | Django 6.0.3 | Redis session backend (redis 7.4.0) | redis:7-alpine |
| `useEffect` + `setInterval` heartbeat | React 18.3.1 | Browsers modernos (ES2020+) | Chrome 120+, Firefox 121+, Safari 17+ |
| Session Expiry Overlay | React 18.3.1 | Vite 5.4.1 + TypeScript 5.5.3 | @rid/rockitdown build pipeline |

---

## 7. Licenças

| Componente | Licença | Compatível com uso comercial SaaS? |
|-----------|---------|:----------------------------------:|
| Traefik v3.3.6 | MIT | Sim |
| Docker Engine (runtime) | Apache 2.0 | Sim |
| Auth Check Endpoint (código próprio) | Proprietário RID | — |
| Session Expiry Overlay (código próprio) | Proprietário RID | — |
| Error Page Template (código próprio) | Proprietário RID | — |

> Nenhuma dependência nova introduz licença copyleft (GPL/AGPL). Nenhuma alteração de licença
> no stack existente.

---

## 8. Impacto no docker-compose.yml

### 8.1 Novo serviço `traefik`

```yaml
# Adicionar dentro de services:, dentro do perfil langflow
traefik:
  image: traefik:v3.3.6
  container_name: rid-traefik
  restart: unless-stopped
  profiles:
    - langflow
  command:
    - "--providers.docker=true"
    - "--providers.docker.exposedByDefault=false"
    - "--providers.docker.network=rid-network"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--log.level=INFO"
    - "--accesslog=true"
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - "/var/run/docker.sock:/var/run/docker.sock:ro"
    - "./certs:/certs:ro"          # certificados TLS (staging/produção)
  networks:
    - rid-network
```

> O socket Docker (`/var/run/docker.sock:ro`) é montado em modo read-only — Traefik
> necessita apenas de leitura para descoberta de serviços via labels.
> Seguindo o standard devops.md: container executa como não-root (Traefik v3 por defeito).

### 8.2 Alterações ao serviço `langflow`

```yaml
# REMOVER:
ports:
  - "7861:7860"

# ADICIONAR em environment:
LANGFLOW_BASE_URL: "http://langflow:7860"
LANGFLOW_CORS_ORIGINS: "https://app.rid.example.com"

# ADICIONAR labels:
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.langflow.rule=PathPrefix(`/flows`)"
  - "traefik.http.routers.langflow.entrypoints=websecure"
  - "traefik.http.routers.langflow.tls=true"
  - "traefik.http.routers.langflow.middlewares=rid-auth@docker,langflow-ws@docker"
  - "traefik.http.services.langflow.loadbalancer.server.port=7860"
  - "traefik.http.middlewares.rid-auth.forwardauth.address=http://backend:8000/internal/auth-check/"
  - "traefik.http.middlewares.rid-auth.forwardauth.trustForwardHeader=true"
  - "traefik.http.middlewares.rid-auth.forwardauth.authResponseHeaders=X-Auth-User,X-Auth-Tenant"
  - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Connection=keep-alive, Upgrade"
  - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Upgrade=websocket"
```

### 8.3 Alterações ao serviço `backend`

```yaml
# ACTUALIZAR em environment:
DJANGO_ALLOWED_HOSTS: "app.rid.example.com,backend,localhost,127.0.0.1"

# ADICIONAR em environment (produção/staging via .env):
# DJANGO_SECURE_PROXY_SSL_HEADER=true
# DJANGO_SESSION_COOKIE_SECURE=true
# DJANGO_CSRF_COOKIE_SECURE=true
# LANGFLOW_BASE_URL=http://langflow:7860

# Labels (opcional — apenas se o backend for exposto via Traefik publicamente):
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.backend.rule=Host(`app.rid.example.com`) && !PathPrefix(`/flows`)"
  - "traefik.http.routers.backend.entrypoints=websecure"
  - "traefik.http.routers.backend.tls=true"
  - "traefik.http.services.backend.loadbalancer.server.port=8000"
```

### 8.4 Resumo de alterações por serviço

| Serviço | Tipo de alteração | Detalhe |
|---------|------------------|---------|
| `traefik` | **Novo serviço** | Container edge router, perfil `langflow`, rede `rid-network` |
| `langflow` | Remoção de porta | `7861:7860` removido |
| `langflow` | Actualização de env | `LANGFLOW_BASE_URL` → hostname interno; `LANGFLOW_CORS_ORIGINS` actualizado |
| `langflow` | Adição de labels | Router, middleware forwardAuth, serviço interno, WebSocket headers |
| `backend` | Actualização de env | `DJANGO_ALLOWED_HOSTS` + proxy SSL headers + session secure flags |
| `langflow-pg-bootstrap` | Sem alteração | Não afectado |
| `db` | Sem alteração | Não afectado |
| `redis` | Sem alteração | Não afectado |

---

## 9. Gate 6 Validation Checklist

| Categoria | Verificação | Estado |
|-----------|-------------|:------:|
| **Versões exactas** | Traefik `v3.3.6` — sem `latest`, sem ranges | PASS |
| **Versões exactas** | Nenhuma dependência Python nova introduzida | PASS |
| **Versões exactas** | Nenhuma dependência npm nova introduzida | PASS |
| **CVE** | CVE check realizado para Traefik v3.3.6 | PASS |
| **CVE** | Nenhum CVE crítico (CVSS >= 9.0) confirmado em v3.3.6 | PASS |
| **CVE** | Acção definida: `docker scout cves` no pipeline CI antes de deploy | PASS |
| **Licenças** | Traefik — MIT — compatível com SaaS comercial | PASS |
| **Licenças** | Nenhuma nova licença copyleft introduzida | PASS |
| **Scope** | Só documenta o que este feature ADICIONA — stack existente não re-documentado | PASS |
| **Rastreabilidade** | Todas as secções referenciam o TRD (componentes, ADRs, decisões) | PASS |
| **Docker** | Imagem Traefik com versão pinada (`traefik:v3.3.6`) | PASS |
| **Docker** | Socket Docker montado em modo read-only (`:ro`) | PASS |
| **Docker** | Container Traefik no perfil `langflow` (não activo por defeito) | PASS |
| **Docker** | Porta pública Langflow (`7861:7860`) removida do serviço | PASS |
| **Docker** | `exposedByDefault=false` — nenhum serviço exposto sem label explícita | PASS |
| **Config** | `.env` e `.env.example` actualizados (sem valores inline no docker-compose) | A FAZER (implementação) |
| **Config** | `LANGFLOW_BASE_URL` actualizado para hostname interno | PASS (documentado) |
| **Config** | Django proxy settings documentados (`SECURE_PROXY_SSL_HEADER`, etc.) | PASS |
| **Frontend** | Heartbeat implementado sem dependências npm novas | PASS |
| **Frontend** | Hook extraído em ficheiro separado (`useSessionHeartbeat.ts`) | PASS (especificado) |
| **Frontend** | WCAG 2.1 AA especificado para Session Expiry Overlay | PASS |
| **Alternativas** | Alternativas ao Traefik avaliadas e rejeitadas com justificação | PASS |
| **Compatibilidade** | Matriz de compatibilidade completa | PASS |

**Resultado Gate 6: PASS — Pronto para task breakdown.**

> Único item "A FAZER": actualização do `.env.example` durante a fase de implementação (Gate 7+).
> Não bloqueia Gate 6 — é uma acção de implementação, não de design.

---

## 10. Próximo passo

**Gate 7 — Task Breakdown**

Skill: `ring-pm-team:pre-dev-task-breakdown`

O Task Breakdown deve cobrir:

1. Implementação do Auth Check Endpoint Django (`/internal/auth-check/`)
2. Adição do serviço Traefik ao `docker-compose.yml` com labels forwardAuth
3. Remoção da porta pública `7861:7860` do serviço Langflow
4. Actualização de variáveis de ambiente Django (proxy headers, session secure, ALLOWED_HOSTS)
5. Actualização de `LANGFLOW_BASE_URL` e `LANGFLOW_CORS_ORIGINS`
6. Implementação do `useSessionHeartbeat` hook e Session Expiry Overlay
7. Implementação do Error Page Template Django
8. Actualização do `.env.example` com todas as novas variáveis
9. Testes: unitários (Auth Check), integração (forwardAuth flow), WCAG (overlay + error page)
