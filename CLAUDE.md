# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

```bash
# Environment
make up              # Start PostgreSQL (port 5433) + Redis via Docker
make down            # Stop all containers
make dev-setup       # Install backend deps via uv

# Backend dev server (from backend/)
uvicorn core.asgi:application --reload --port 8000

# Tests
make test                                          # Full pytest suite
cd backend && uv run pytest tests/test_foo.py -v  # Single test file
cd backend && pytest tests/test_architecture.py -v # ADR compliance (15 tests)

# Lint / Format
make lint    # ruff check --fix
make format  # ruff format

# Migrations
make migrate-up                  # Apply pending migrations
make migrate-create NAME=<desc>  # Create new migration

# Frontend build (from frontend/)
pnpm install
pnpm --filter @rid/rockitdown build  # Outputs to backend/static/apps/rockitdown/assets/
```

---

## Architecture

### ASGI Hybrid (ADR-003)

`backend/core/asgi.py` is the root ASGI entrypoint. It routes:
- `lifespan` events → FastAPI
- `/api` and `/api/*` → FastAPI (`api/main.py`)
- Everything else → Django

Both frameworks run in the same process.

### Multi-tenancy (django-tenants)

Each customer gets an isolated PostgreSQL schema. Tenant resolution (`core/tenant_middleware.py`) uses `HeaderFirstTenantMiddleware`:
1. Check `X-Tenant-Id` header (UUID in `Customer.public_tenant_id`) — controlled by `TENANT_RESOLUTION_HEADER` env var
2. Fall back to `Host` header → `Domain` lookup

In `DEBUG=True`, unknown hostnames (e.g. `localhost`, `testserver`) serve the public schema instead of 404.

**Critical split (ADR-002):** `TenantUser` and all auth models live in `SHARED_APPS` (public schema). Tenant-scoped models go in `TENANT_APPS`. Never add user/auth models to `TENANT_APPS`.

### Authentication

`core/auth_backends.py` — `TenantAwareBackend` authenticates via `user@tenant-domain` format (ADR-005). Auth backends order in settings: `TenantAwareBackend` → `allauth.AuthenticationBackend` → `ModelBackend`.

FastAPI dependency `api/deps.py:get_current_tenant` wraps Django ORM calls with `sync_to_async(thread_sensitive=True)` to preserve thread-local tenant context (ADR-001).

### Langflow Integration (ADR-009)

Langflow runs as an internal Docker container (`http://langflow:7860`, not exposed publicly). Access is gated via Traefik `forwardAuth` pointing to `GET /internal/auth-check/` (returns 200/401/403). Django provisions a Langflow workspace per tenant and a Langflow user account per `TenantUser` via `api/services/langflow_client.py` and `api/services/langflow_workspace.py`.

Key env vars for Langflow: `LANGFLOW_BASE_URL`, `LANGFLOW_SUPERUSER_API_KEY` (required for user provisioning), `LANGFLOW_SUPERUSER_PASSWORD` (required in production).

### Frontend (SPA)

`GET /app/` → Django view `apps.accounts.views.RockItDownSPA` (requires login). The view injects `app_config_json` into the template with tenant info, API URLs, and CSRF token. Vite build artifacts go to `backend/static/apps/rockitdown/assets/`; `index.html` remains a Django template.

---

## ADR Compliance (Gate 3.5)

Before modifying critical files, verify an ADR covers the change. Run `cd backend && pytest tests/test_architecture.py -v` to audit ADR-001 through ADR-006.

Files requiring ADR verification:

| File / Path | ADR |
|---|---|
| `backend/api/deps.py` | ADR-001 |
| `backend/core/settings.py` — SHARED_APPS/TENANT_APPS | ADR-002 |
| `backend/core/asgi.py` | ADR-003 |
| `backend/apps/tenants/services.py` | ADR-004 |
| `backend/core/auth_backends.py` | ADR-005 |
| `docker-compose.yml` — ports | ADR-006 |
| `backend/apps/*/models.py` (user models) | ADR-002 |

New ADRs go in `docs/adr/ADR-{NNN}-{slug}.md` using `docs/adr/TEMPLATE.md`. Add to `docs/adr/README.md` index.

---

## Testing Conventions

- `asyncio_mode = auto` (pytest-asyncio) — async tests work without decorators
- Async tests hitting the DB: `@pytest.mark.django_db(transaction=True)`
- ASGI test client: `AsyncClient` with `ASGITransport` (see `backend/tests/conftest.py`)
- Test files live in `backend/tests/test_*.py`

---

## Key Environment Variables

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Required |
| `DATABASE_PORT` | `5433` in Docker (ADR-006, avoids conflict with local PostgreSQL) |
| `LANGFLOW_SUPERUSER_PASSWORD` | Required in production |
| `LANGFLOW_SUPERUSER_API_KEY` | Required for user provisioning (graceful degradation if absent) |
| `STRIPE_SECRET_KEY` | Must be `sk_live_*` in production |
| `REDIS_URL` | Redis cache + sessions |
| `TENANT_RESOLUTION_HEADER` | Set to empty to disable header-based tenant resolution |
| `DJANGO_SHOW_PUBLIC_IF_NO_TENANT` | `true` in dev; never set in production |

---

## Commit Convention

Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`. Use `/ring:commit` if the Ring plugin is active.

---

## Docs / ADRs / PMO

- ADRs: `docs/adr/` — immutable once `Accepted`; create new ADR to supersede
- Architecture plans: `docs/plans/`
- Feature pre-dev docs: `docs/pre-dev/{feature}/`
- Ring agent/skill library: `ring/` (vendored; see `ring/CLAUDE.md` for Ring-specific rules)
- PMO artefacts: `pmo/`
