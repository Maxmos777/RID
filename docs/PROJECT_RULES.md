# Project Rules — RID

> Ring Standards são carregados automaticamente pelos agentes via WebFetch.
> Este ficheiro documenta APENAS o que Ring Standards não cobre.
> NÃO duplicar: error handling, logging, testing, architecture, lib-commons.

## Stack tecnológico (não coberto pelo Ring Standards)

| Tecnologia | Versão | Finalidade | Notas |
|------------|--------|-----------|-------|
| Django | 6.0.3 | Application Server | Multi-tenant via django-tenants |
| Traefik | 3.3.6 | Edge Router / Reverse Proxy | forwardAuth middleware |
| Langflow | 1.8.3-rid | Editor de fluxos interno | Acesso apenas via rede interna; imagem `langflowai/langflow:1.8.3-rid` |
| React | 18.3.1 | Frontend shell | Raw React, sem UI library |
| django-tenants | 3.10.1 | Multi-tenancy | HeaderFirstTenantMiddleware |
| PostgreSQL | (stack existente) | Base de dados principal | Versão não fixada neste feature |
| Docker Compose | v2.x | Orquestração local | Profile: langflow |

## Multi-tenancy

- **Middleware:** `HeaderFirstTenantMiddleware` (não o stock `TenantMainMiddleware`)
- **Resolução de tenant:** Lê `Host` header → mapeia para schema PostgreSQL
- **Modelo:** `TenantMembership` em `apps/accounts/`
- **Contexto:** `connection.schema_name` para obter tenant activo
- **Traefik forwardAuth:** DEVE passar `Host: $host` para preservar resolução de tenant

## Estrutura de directórios não-standard

| Directório | Finalidade | Padrão |
|------------|-----------|--------|
| `apps/` | Django apps (accounts, etc.) | Django app structure |
| `frontend/` | React 18 shell | Raw React, Vite |
| `infra/` ou raiz | docker-compose.yml | Docker Compose |

## Integrações externas

| Serviço | Finalidade | Notas |
|---------|-----------|-------|
| Langflow (interno) | Editor de fluxos | Container interno, porta 7860 (não exposta) |
| Traefik | Reverse proxy | Container Docker, porta 80 pública |

## Variáveis de ambiente relevantes

| Variável | Finalidade | Exemplo |
|----------|-----------|---------|
| `TRAEFIK_AUTH_URL` | URL do Auth Check Endpoint para forwardAuth | `http://web:8000/internal/auth-check/` |
| `LANGFLOW_INTERNAL_URL` | URL interna do Langflow | `http://langflow:7860` |
| `DJANGO_SETTINGS_MODULE` | Módulo de settings activo | `config.settings.production` |
| `SECURE_PROXY_SSL_HEADER` | Header para HTTPS via proxy | `HTTP_X_FORWARDED_PROTO,https` |

## Terminologia de domínio

| Termo | Definição | Usado em |
|-------|----------|---------|
| Tenant | Organização/cliente isolado | Todas as apps |
| Auth Gate | Perímetro de autenticação para o editor | TRD, subtasks |
| Auth Check Endpoint | `GET /internal/auth-check/` — 200/401/403 | T-003, T-005 |
| Error Page | Página de erro RID quando Langflow indisponível | T-004 |
| Session Overlay | Componente React para sessão expirada | T-005 |
| Heartbeat | Polling periódico a cada 120s ao auth-check | T-005 |
| forwardAuth | Middleware Traefik que valida sessão via sub-request | T-001 |
| HeaderFirstTenantMiddleware | Middleware django-tenants que lê tenant do Host header | T-002, T-003 |

## Feature em desenvolvimento

**Feature:** `rid-langflow-single-entry`
**Docs:** `/home/RID/docs/pre-dev/rid-langflow-single-entry/`
**Tasks:** `gate-7-tasks.md` (T-001 a T-006)
**Subtasks:** `gate-8-subtasks/T-NNN/`

*Gerado de: gate-1-prd.md, gate-3-trd.md, gate-6-dependency-map.md*
*Data: 2026-04-06*
