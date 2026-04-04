# RID Platform Architecture — Implementation Plan

**Date:** 2026-04-03
**Status:** Ready for execution
**Agent:** ring:write-plan

---

## Goal

Build the RID SaaS platform: a multi-tenant Django + FastAPI backend with Langflow AI workflow integration, a React SPA frontend, and Stripe billing. Django serves SPA entry points; FastAPI handles all `/api/*` routes via ASGI mounting; Langflow runs in Docker with auto-login bridging.

---

## Architecture Summary

```
/home/RID/
├── backend/                          ← Django + FastAPI (uv, Python 3.12)
│   ├── core/                         ← Django project package
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── tenants/                  ← django-tenants models
│   │   └── accounts/                 ← allauth + TenantUser
│   ├── api/                          ← FastAPI app
│   │   ├── main.py
│   │   └── routers/
│   │       ├── langflow_auth.py
│   │       └── tenant.py
│   ├── templates/
│   │   └── apps/
│   │       └── rockitdown/
│   │           └── index.html
│   ├── staticfiles/
│   ├── manage.py
│   ├── pyproject.toml
│   └── .env
├── frontend/                         ← pnpm workspaces monorepo
│   ├── package.json
│   ├── pnpm-workspace.yaml
│   ├── packages/
│   │   └── shared/                   ← design tokens, types, utils
│   └── apps/
│       ├── rockitdown/               ← main SPA
│       └── langflow-embed/           ← Langflow wrapper SPA
├── docker/
│   ├── docker-compose.yml
│   └── nginx/
│       └── nginx.conf
└── docs/
    └── plans/
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.12 via uv |
| Web framework | Django 6 + FastAPI |
| ASGI server | Uvicorn |
| Database | PostgreSQL (multi-tenant schemas) |
| Multi-tenancy | django-tenants |
| Auth | django-allauth |
| Cache / pub-sub | Redis |
| AI workflows | Langflow (Docker) |
| Frontend | React 18 + Vite + TypeScript |
| Package manager | pnpm workspaces |
| Billing | Stripe |
| Proxy | Nginx |

---

## Phase 1: Backend Foundation

### Task 1.1 — Django project skeleton

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript (general-purpose Python)
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/core/__init__.py`
- `/home/RID/backend/core/settings.py`
- `/home/RID/backend/core/urls.py`
- `/home/RID/backend/core/asgi.py`
- `/home/RID/backend/manage.py`

**Instructions:**

First, add the missing dependencies to `pyproject.toml`:

```bash
cd /home/RID/backend
uv add django-tenants django-allauth[socialaccount] redis httpx stripe
```

Create `/home/RID/backend/core/__init__.py`:
```python
```

Create `/home/RID/backend/manage.py`:
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

Create `/home/RID/backend/.env`:
```
DJANGO_SECRET_KEY=dev-insecure-change-in-production-please-do-not-use-this
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://rid:rid@localhost:5432/rid
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=rid
DATABASE_USER=rid
DATABASE_PASSWORD=rid

REDIS_URL=redis://localhost:6379/0

LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=adminpassword

STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
```

**Verification:**
```bash
cd /home/RID/backend
uv run python manage.py --help
# Expected: Django management command list printed without ImportError
```

---

### Task 1.2 — Django settings

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Files to Create:**
- `/home/RID/backend/core/settings.py`

**Complete file content:**

```python
"""
Django settings for RID platform.

Multi-tenant via django-tenants (schema-per-tenant).
FastAPI mounted at /api/* via ASGI.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# ---------------------------------------------------------------------------
# django-tenants: MUST be first in INSTALLED_APPS
# ---------------------------------------------------------------------------
SHARED_APPS = [
    "django_tenants",           # must be first
    "apps.tenants",             # contains Customer + Domain models
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "apps.accounts",            # TenantUser lives here (shared table)
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenants.Customer"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ---------------------------------------------------------------------------
# Database — django-tenants requires django.db.backends.postgresql
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.getenv("DATABASE_NAME", "rid"),
        "USER": os.getenv("DATABASE_USER", "rid"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "rid"),
        "HOST": os.getenv("DATABASE_HOST", "localhost"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
    }
}

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# ---------------------------------------------------------------------------
# Cache — Redis
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    }
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Langflow
# ---------------------------------------------------------------------------
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://localhost:7860")
LANGFLOW_SUPERUSER = os.getenv("LANGFLOW_SUPERUSER", "admin")
LANGFLOW_SUPERUSER_PASSWORD = os.getenv("LANGFLOW_SUPERUSER_PASSWORD", "adminpassword")

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "import django; import os; os.environ['DJANGO_SETTINGS_MODULE']='core.settings'; django.setup(); print('settings OK')"
# Expected: settings OK
```

---

### Task 1.3 — ASGI mounting: FastAPI inside Django

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/core/asgi.py`

**Complete file content:**

```python
"""
ASGI config for RID project.

FastAPI is mounted at /api using Starlette's Mount, so Django handles
everything else (templates, admin, allauth).

Execution order:
  1. Request arrives at Uvicorn
  2. DispatchMiddleware routes /api/* → FastAPI app
  3. Everything else → Django ASGI app
"""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Django MUST be set up before importing FastAPI app (which imports Django models)
django_app = get_asgi_application()

from api.main import create_app  # noqa: E402  (import after django setup)

fastapi_app = create_app()


async def application(scope, receive, send):  # type: ignore[no-untyped-def]
    """
    Root ASGI application.

    Routes /api/* to FastAPI, everything else to Django.
    Uses raw ASGI dispatch instead of Starlette Mount so Django's
    middleware stack (including TenantMainMiddleware) is unaffected.
    """
    path: str = scope.get("path", "")

    if path.startswith("/api/"):
        # Strip the leading empty segment; FastAPI router paths start with /
        await fastapi_app(scope, receive, send)
    else:
        await django_app(scope, receive, send)
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
from core.asgi import application
print(type(application))
"
# Expected: <class 'function'>
```

---

### Task 1.4 — django-tenants models

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Files to Create:**
- `/home/RID/backend/apps/__init__.py`
- `/home/RID/backend/apps/tenants/__init__.py`
- `/home/RID/backend/apps/tenants/apps.py`
- `/home/RID/backend/apps/tenants/models.py`

Create `/home/RID/backend/apps/__init__.py` (empty).

Create `/home/RID/backend/apps/tenants/__init__.py` (empty).

Create `/home/RID/backend/apps/tenants/apps.py`:
```python
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    label = "tenants"
```

Create `/home/RID/backend/apps/tenants/models.py`:
```python
"""
Multi-tenancy models.

Customer  — the tenant (one PostgreSQL schema per customer)
Domain    — maps hostnames to tenants
"""
from __future__ import annotations

from django_tenants.models import DomainMixin, TenantMixin


class Customer(TenantMixin):
    """
    One row per tenant.  django-tenants creates/drops the PostgreSQL schema
    automatically when this model is saved/deleted.

    auto_create_schema = True means django-tenants runs migrations for the
    new schema immediately on Customer.save().
    """

    auto_create_schema = True

    class Meta:
        app_label = "tenants"

    def __str__(self) -> str:
        return self.schema_name


class Domain(DomainMixin):
    """
    Maps a hostname (e.g. acme.rockitdown.com) to a Customer schema.
    is_primary=True marks the canonical domain used for redirects.
    """

    class Meta:
        app_label = "tenants"

    def __str__(self) -> str:
        return self.domain
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.tenants.models import Customer, Domain
print('Customer:', Customer)
print('Domain:', Domain)
"
# Expected:
# Customer: <class 'apps.tenants.models.Customer'>
# Domain: <class 'apps.tenants.models.Domain'>
```

---

### Task 1.5 — Initial Django migrations

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Prerequisite:** PostgreSQL must be running and the `rid` database + user must exist.

```bash
# Create DB if it doesn't exist yet
createdb rid -U postgres 2>/dev/null || true
psql -U postgres -c "CREATE USER rid WITH PASSWORD 'rid';" 2>/dev/null || true
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE rid TO rid;" 2>/dev/null || true
```

**Instructions:**
```bash
cd /home/RID/backend
uv run python manage.py makemigrations tenants
uv run python manage.py migrate_schemas --shared
```

**Verification:**
```bash
cd /home/RID/backend
uv run python manage.py migrate_schemas --shared --list 2>&1 | grep -E "\[X\]|OK"
# Expected: migration rows prefixed with [X] (applied)
```

---

## Phase 2: FastAPI API Layer

### Task 2.1 — FastAPI app setup

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/api/__init__.py`
- `/home/RID/backend/api/main.py`
- `/home/RID/backend/api/deps.py`

Create `/home/RID/backend/api/__init__.py` (empty).

Create `/home/RID/backend/api/main.py`:
```python
"""
FastAPI application factory.

Mounted at /api/ by core/asgi.py.  All routers are registered here.
Lifespan events handle startup/shutdown side-effects without blocking.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import langflow_auth, tenant


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title="RID API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(langflow_auth.router, prefix="/api/v1/langflow", tags=["langflow"])
    app.include_router(tenant.router, prefix="/api/v1/tenants", tags=["tenants"])

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

Create `/home/RID/backend/api/deps.py`:
```python
"""
FastAPI dependency injection helpers.

get_django_user  — resolves the authenticated Django user from the session
                   cookie present in the incoming request.
get_current_tenant — returns the active django-tenants tenant from the
                     request hostname.
"""
from __future__ import annotations

from typing import Annotated

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from fastapi import Depends, HTTPException, Request, status

User = get_user_model()


async def get_django_user(request: Request):  # type: ignore[return]
    """
    Extract the authenticated Django user from the signed session cookie.

    Django's session middleware is NOT active for FastAPI requests, so we
    decode the session manually using Django's session engine.
    """
    import django.contrib.sessions.backends.db as session_backend
    from django.conf import settings

    session_key = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        session = session_backend.SessionStore(session_key)
        user_id = session.get("_auth_user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        user = await User.objects.aget(pk=user_id)
    except User.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


AuthenticatedUser = Annotated[User, Depends(get_django_user)]
```

Create `/home/RID/backend/api/routers/__init__.py` (empty).

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from api.main import create_app
app = create_app()
routes = [r.path for r in app.routes]
print(routes)
"
# Expected: list containing '/api/health', '/api/v1/langflow/...', '/api/v1/tenants/...'
```

---

### Task 2.2 — Langflow auto-login endpoint

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 5 min

**Files to Create:**
- `/home/RID/backend/api/routers/langflow_auth.py`
- `/home/RID/backend/api/services/langflow_client.py`

Create `/home/RID/backend/api/services/__init__.py` (empty).

Create `/home/RID/backend/api/services/langflow_client.py`:
```python
"""
Langflow HTTP client.

Wraps Langflow's REST API:
  POST /api/v1/login          → get superuser JWT
  POST /api/v1/users/         → create a new Langflow user
  GET  /api/v1/users/whoami   → verify a JWT is still valid
  POST /api/v1/api_key/       → create an API key for a user

All methods return (result, error) tuples — no exceptions propagate out.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from django.conf import settings


async def _get_superuser_token() -> tuple[str, str | None]:
    """Return (jwt_token, error).  Uses Langflow's form-based login."""
    async with httpx.AsyncClient(base_url=settings.LANGFLOW_BASE_URL, timeout=10) as client:
        resp = await client.post(
            "/api/v1/login",
            data={
                "username": settings.LANGFLOW_SUPERUSER,
                "password": settings.LANGFLOW_SUPERUSER_PASSWORD,
            },
        )
    if resp.status_code != 200:
        return "", f"langflow superuser login failed: {resp.status_code} {resp.text}"
    payload = resp.json()
    token: str = payload.get("access_token", "")
    return token, None


async def get_or_create_langflow_user(
    email: str,
    password: str,
) -> tuple[dict[str, Any], str | None]:
    """
    Ensure a Langflow user exists for the given email.

    Returns ({'access_token': ..., 'api_key': ...}, None) on success.
    Returns ({}, error_message) on failure.
    """
    superuser_token, err = await _get_superuser_token()
    if err:
        return {}, err

    headers = {"Authorization": f"Bearer {superuser_token}"}

    async with httpx.AsyncClient(base_url=settings.LANGFLOW_BASE_URL, timeout=10) as client:
        # Try to create; if 400 (already exists) that's fine — proceed to login
        create_resp = await client.post(
            "/api/v1/users/",
            json={"username": email, "password": password},
            headers=headers,
        )
        if create_resp.status_code not in (200, 201, 400):
            return {}, f"create user failed: {create_resp.status_code} {create_resp.text}"

        # Login as the user to get their JWT
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": email, "password": password},
        )
        if login_resp.status_code != 200:
            return {}, f"user login failed: {login_resp.status_code} {login_resp.text}"

        user_token: str = login_resp.json().get("access_token", "")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Create or retrieve an API key for this user
        key_resp = await client.post(
            "/api/v1/api_key/",
            json={"name": "rid-auto"},
            headers=user_headers,
        )
        api_key = ""
        if key_resp.status_code in (200, 201):
            api_key = key_resp.json().get("api_key", "")

    return {"access_token": user_token, "api_key": api_key}, None
```

Create `/home/RID/backend/api/routers/langflow_auth.py`:
```python
"""
Langflow auto-login router.

GET /api/v1/langflow/auth/auto-login
  → requires Django session auth
  → get_or_create_langflow_user for the Django user
  → returns JWT + api_key
  → frontend stores tokens in httpOnly cookies

This is the proven auto-login bridge pattern from /home/RockItDown.
"""
from __future__ import annotations

import hashlib
import secrets

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.deps import AuthenticatedUser
from api.services.langflow_client import get_or_create_langflow_user
from apps.accounts.models import TenantUser

router = APIRouter()


class AutoLoginResponse(BaseModel):
    access_token: str
    api_key: str


def _derive_langflow_password(user_id: int, secret_suffix: str = "rid-lf-v1") -> str:
    """
    Deterministically derive a Langflow password from the Django user PK.

    Uses HMAC-like construction so the password is stable across requests
    but never stored in plaintext anywhere.
    """
    raw = f"{user_id}:{secret_suffix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.get("/auth/auto-login", response_model=AutoLoginResponse)
async def auto_login(current_user: AuthenticatedUser) -> AutoLoginResponse:
    """
    Bridge endpoint: exchanges Django session for Langflow credentials.

    1. Look up TenantUser for this Django user.
    2. If Langflow credentials already cached → return them.
    3. Otherwise call get_or_create_langflow_user and persist.
    """
    try:
        tenant_user = await TenantUser.objects.aget(user=current_user)
    except TenantUser.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TenantUser profile not found for this user",
        )

    # Return cached credentials if present
    if tenant_user.langflow_api_key and tenant_user.langflow_user_id:
        # Re-login to get a fresh JWT (API keys don't expire but JWTs do)
        email = current_user.email
        password = _derive_langflow_password(current_user.pk)
        result, err = await get_or_create_langflow_user(email, password)
        if err:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=err)
        return AutoLoginResponse(
            access_token=result["access_token"],
            api_key=tenant_user.langflow_api_key,
        )

    # First time: create + store
    email = current_user.email
    password = _derive_langflow_password(current_user.pk)
    result, err = await get_or_create_langflow_user(email, password)
    if err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=err)

    tenant_user.langflow_api_key = result.get("api_key", "")
    # langflow_user_id = email (Langflow uses email as username)
    tenant_user.langflow_user_id = email
    await tenant_user.asave(update_fields=["langflow_api_key", "langflow_user_id"])

    return AutoLoginResponse(
        access_token=result["access_token"],
        api_key=tenant_user.langflow_api_key,
    )
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from api.routers.langflow_auth import router
print([r.path for r in router.routes])
"
# Expected: ['/auth/auto-login']
```

---

### Task 2.3 — Tenant middleware for FastAPI

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/api/routers/tenant.py`

```python
"""
Tenant router — exposes tenant-scoped info to the frontend.

GET  /api/v1/tenants/current   → returns schema_name, domain, plan
POST /api/v1/tenants/          → create new tenant (admin only, used by onboarding)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter()


class TenantInfo(BaseModel):
    schema_name: str
    domain: str
    plan: str


@router.get("/current", response_model=TenantInfo)
async def current_tenant(request: Request) -> TenantInfo:
    """
    Return the current tenant context.

    django-tenants sets the active schema via TenantMainMiddleware, which
    runs before FastAPI receives the request (it's a Django ASGI middleware
    in the outer application).  The active connection schema can be read
    from Django's db connection.

    For FastAPI requests that pass through Django's ASGI chain the tenant
    is already active — we read it from the thread-local db connection.
    """
    from django.db import connection

    schema = getattr(connection, "schema_name", "public")
    if schema == "public":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context active for this request",
        )

    try:
        from apps.tenants.models import Customer, Domain

        customer = await Customer.objects.aget(schema_name=schema)
        domain_obj = await Domain.objects.filter(tenant=customer, is_primary=True).afirst()
        domain = domain_obj.domain if domain_obj else schema
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tenant info: {exc}",
        ) from exc

    return TenantInfo(
        schema_name=schema,
        domain=domain,
        plan=getattr(customer, "plan", "free"),
    )
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from api.routers.tenant import router
print('tenant router loaded:', router.prefix if hasattr(router, 'prefix') else 'ok')
"
# Expected: tenant router loaded: ok
```

---

## Phase 3: Django Template + SPA Serving

### Task 3.1 — Django URL routing for SPAs

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 2 min

**Files to Create:**
- `/home/RID/backend/core/urls.py`

```python
"""
Root URL configuration.

/           → redirect to /app/
/app/       → RockItDown SPA (LoginRequired)
/langflow/  → served by Nginx proxy (see docker/nginx/nginx.conf)
/admin/     → Django admin
/accounts/  → django-allauth
/api/       → FastAPI (handled in asgi.py before URL routing)
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.views import RockItDownSPA

urlpatterns = [
    path("", RedirectView.as_view(url="/app/", permanent=False)),
    path("app/", RockItDownSPA.as_view(), name="rockitdown-spa"),
    # django-allauth handles login / signup / email confirmation
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
]
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from django.urls import reverse
print(reverse('rockitdown-spa'))
"
# Expected: /app/
```

---

### Task 3.2 — SPA views with context injection

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/apps/accounts/__init__.py`
- `/home/RID/backend/apps/accounts/apps.py`
- `/home/RID/backend/apps/accounts/models.py`
- `/home/RID/backend/apps/accounts/views.py`
- `/home/RID/backend/apps/accounts/admin.py`

Create `/home/RID/backend/apps/accounts/__init__.py` (empty).

Create `/home/RID/backend/apps/accounts/apps.py`:
```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
```

Create `/home/RID/backend/apps/accounts/models.py`:
```python
"""
TenantUser — per-user profile that stores Langflow credentials.

Lives in the shared schema (listed in SHARED_APPS) so it's accessible
regardless of which tenant schema is active.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TenantUser(models.Model):
    """
    Extends the Django User with Langflow-specific fields.

    langflow_user_id  — the email/username used in Langflow
    langflow_api_key  — API key created in Langflow for this user
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tenant_profile")
    langflow_user_id = models.CharField(max_length=255, blank=True, default="")
    langflow_api_key = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "accounts"
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"

    def __str__(self) -> str:
        return f"TenantUser({self.user.email})"

    @property
    def has_langflow_credentials(self) -> bool:
        return bool(self.langflow_user_id and self.langflow_api_key)
```

Create `/home/RID/backend/apps/accounts/views.py`:
```python
"""
SPA entry point views.

Each view:
  1. Enforces login (LoginRequiredMixin)
  2. Renders a Django template that loads the React bundle
  3. Injects server-side context (tenant info, API config, CSRF token)
     as a JSON blob in <script id="app-config"> so React can bootstrap
     without an extra API round-trip.
"""
from __future__ import annotations

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.middleware.csrf import get_token
from django.views.generic import TemplateView


class RockItDownSPA(LoginRequiredMixin, TemplateView):
    template_name = "apps/rockitdown/index.html"

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        request = self.request

        # Resolve tenant schema from active DB connection
        from django.db import connection
        schema_name = getattr(connection, "schema_name", "public")

        tenant_info: dict[str, str] = {
            "schema_name": schema_name,
            "user_email": request.user.email,
            "user_id": str(request.user.pk),
        }

        api_config: dict[str, str] = {
            "base_url": "/api/v1",
            "langflow_auto_login_url": "/api/v1/langflow/auth/auto-login",
            "langflow_base_url": settings.LANGFLOW_BASE_URL,
        }

        ctx["app_config_json"] = json.dumps({
            "tenant": tenant_info,
            "api": api_config,
            "csrf_token": get_token(request),
        })
        return ctx
```

Create `/home/RID/backend/apps/accounts/admin.py`:
```python
from django.contrib import admin

from .models import TenantUser


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ("user", "langflow_user_id", "has_langflow_credentials", "created_at")
    search_fields = ("user__email", "langflow_user_id")
    readonly_fields = ("created_at", "updated_at")
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.accounts.models import TenantUser
from apps.accounts.views import RockItDownSPA
print('TenantUser:', TenantUser)
print('RockItDownSPA template:', RockItDownSPA.template_name)
"
# Expected:
# TenantUser: <class 'apps.accounts.models.TenantUser'>
# RockItDownSPA template: apps/rockitdown/index.html
```

---

### Task 3.3 — Django templates for SPAs

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/templates/base.html`
- `/home/RID/backend/templates/apps/rockitdown/index.html`

Create `/home/RID/backend/templates/base.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  {% load static %}
  <title>{% block title %}RID Platform{% endblock %}</title>
  {% block head_extra %}{% endblock %}
</head>
<body>
  {% block body %}{% endblock %}
</body>
</html>
```

Create `/home/RID/backend/templates/apps/rockitdown/index.html`:
```html
{% extends "base.html" %}
{% load static %}

{% block title %}RockItDown{% endblock %}

{% block head_extra %}
  {# Vite build injects a hashed bundle — the build script copies it here. #}
  {# During local dev with `vite dev`, the dev server runs on :5173        #}
  <link rel="stylesheet" href="{% static 'apps/rockitdown/assets/index.css' %}" />
{% endblock %}

{% block body %}
  {#
    Server-injected bootstrap config.
    React reads this in main.tsx before rendering to avoid an extra API call.
    The `app_config_json` value is produced by RockItDownSPA.get_context_data().
  #}
  <script id="app-config" type="application/json">
    {{ app_config_json }}
  </script>

  <div id="root"></div>

  <script type="module" src="{% static 'apps/rockitdown/assets/index.js' %}"></script>
{% endblock %}
```

**Verification:**
```bash
cd /home/RID/backend
test -f templates/base.html && echo "base.html OK"
test -f templates/apps/rockitdown/index.html && echo "spa template OK"
# Expected:
# base.html OK
# spa template OK
```

---

### Task 3.4 — Accounts migrations

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 2 min

**Instructions:**
```bash
cd /home/RID/backend
uv run python manage.py makemigrations accounts
uv run python manage.py migrate_schemas --shared
```

**Verification:**
```bash
cd /home/RID/backend
uv run python manage.py showmigrations accounts
# Expected: [X] 0001_initial
```

---

## Phase 4: Frontend Monorepo

### Task 4.1 — pnpm workspaces monorepo root

**Target:** frontend
**Working Directory:** `/home/RID/frontend`
**Agent:** ring:frontend-engineer
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/frontend/package.json`
- `/home/RID/frontend/pnpm-workspace.yaml`
- `/home/RID/frontend/.gitignore`

**Prerequisite:** `pnpm` must be installed. If not: `npm install -g pnpm`

Create `/home/RID/frontend/pnpm-workspace.yaml`:
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

Create `/home/RID/frontend/package.json`:
```json
{
  "name": "rid-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev:rockitdown": "pnpm --filter @rid/rockitdown dev",
    "build:rockitdown": "pnpm --filter @rid/rockitdown build",
    "build:all": "pnpm --filter './apps/*' build",
    "lint": "pnpm -r lint",
    "typecheck": "pnpm -r typecheck"
  },
  "engines": {
    "node": ">=20",
    "pnpm": ">=9"
  }
}
```

Create `/home/RID/frontend/.gitignore`:
```
node_modules/
dist/
.env.local
*.local
```

**Verification:**
```bash
cd /home/RID/frontend
pnpm install 2>&1 | tail -5
# Expected: "Done" or similar — no errors
```

---

### Task 4.2 — packages/shared setup

**Target:** frontend
**Working Directory:** `/home/RID/frontend`
**Agent:** ring:frontend-engineer
**Time estimate:** 4 min

**Files to Create:**
- `/home/RID/frontend/packages/shared/package.json`
- `/home/RID/frontend/packages/shared/tsconfig.json`
- `/home/RID/frontend/packages/shared/src/index.ts`
- `/home/RID/frontend/packages/shared/src/types.ts`
- `/home/RID/frontend/packages/shared/src/tokens.ts`

Create `/home/RID/frontend/packages/shared/package.json`:
```json
{
  "name": "@rid/shared",
  "version": "0.1.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts"
  }
}
```

Create `/home/RID/frontend/packages/shared/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "outDir": "./dist"
  },
  "include": ["src"]
}
```

Create `/home/RID/frontend/packages/shared/src/types.ts`:
```typescript
/**
 * Shared TypeScript types used across all RID frontend apps.
 *
 * AppConfig is injected server-side by Django's RockItDownSPA view
 * and read from <script id="app-config"> in the HTML entry point.
 */

export interface TenantInfo {
  schema_name: string;
  user_email: string;
  user_id: string;
}

export interface ApiConfig {
  base_url: string;
  langflow_auto_login_url: string;
  langflow_base_url: string;
}

export interface AppConfig {
  tenant: TenantInfo;
  api: ApiConfig;
  csrf_token: string;
}

export interface LangflowCredentials {
  access_token: string;
  api_key: string;
}
```

Create `/home/RID/frontend/packages/shared/src/tokens.ts`:
```typescript
/**
 * Design tokens — single source of truth for colours, spacing, typography.
 * Import into Tailwind config or CSS-in-JS as needed.
 */

export const colors = {
  brand: {
    50: "#eff6ff",
    100: "#dbeafe",
    500: "#3b82f6",
    600: "#2563eb",
    900: "#1e3a8a",
  },
  neutral: {
    50: "#f9fafb",
    100: "#f3f4f6",
    700: "#374151",
    900: "#111827",
  },
} as const;

export const spacing = {
  xs: "0.25rem",
  sm: "0.5rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  "2xl": "3rem",
} as const;
```

Create `/home/RID/frontend/packages/shared/src/index.ts`:
```typescript
export * from "./types";
export * from "./tokens";

/**
 * Reads the server-injected AppConfig from the Django template.
 *
 * Django injects a JSON blob into <script id="app-config">.
 * This function parses it once at boot time.
 */
export function readAppConfig(): import("./types").AppConfig {
  const el = document.getElementById("app-config");
  if (!el || !el.textContent) {
    throw new Error("app-config script tag not found — is the Django template correct?");
  }
  return JSON.parse(el.textContent) as import("./types").AppConfig;
}
```

**Verification:**
```bash
cd /home/RID/frontend
node -e "
const ts = require('typescript');
const src = require('fs').readFileSync('packages/shared/src/index.ts', 'utf8');
console.log('shared/src lines:', src.split('\n').length);
"
# Expected: shared/src lines: N (any positive number, no crash)
```

---

### Task 4.3 — apps/rockitdown Vite project

**Target:** frontend
**Working Directory:** `/home/RID/frontend`
**Agent:** ring:frontend-engineer
**Time estimate:** 5 min

**Files to Create:**
- `/home/RID/frontend/apps/rockitdown/package.json`
- `/home/RID/frontend/apps/rockitdown/vite.config.ts`
- `/home/RID/frontend/apps/rockitdown/tsconfig.json`
- `/home/RID/frontend/apps/rockitdown/index.html`
- `/home/RID/frontend/apps/rockitdown/src/main.tsx`
- `/home/RID/frontend/apps/rockitdown/src/App.tsx`
- `/home/RID/frontend/apps/rockitdown/src/hooks/useLangflowAuth.ts`

Create `/home/RID/frontend/apps/rockitdown/package.json`:
```json
{
  "name": "@rid/rockitdown",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build && node scripts/copy-to-django.js",
    "lint": "eslint src",
    "typecheck": "tsc --noEmit",
    "preview": "vite preview"
  },
  "dependencies": {
    "@rid/shared": "workspace:*",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }
}
```

Create `/home/RID/frontend/apps/rockitdown/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

Create `/home/RID/frontend/apps/rockitdown/vite.config.ts`:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@rid/shared": path.resolve(__dirname, "../../packages/shared/src"),
    },
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      output: {
        // Stable filenames so Django {% static %} references don't change
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]",
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to Django/Uvicorn during local dev
      "/api": "http://localhost:8000",
      "/accounts": "http://localhost:8000",
    },
  },
});
```

Create `/home/RID/frontend/apps/rockitdown/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RockItDown</title>
  </head>
  <body>
    <!--
      In production, Django injects <script id="app-config"> before this div.
      In dev (vite dev), we inject a mock config via main.tsx.
    -->
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `/home/RID/frontend/apps/rockitdown/src/main.tsx`:
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// During Vite dev server the Django template is not present,
// so inject a mock app-config if the script tag is missing.
if (!document.getElementById("app-config")) {
  const el = document.createElement("script");
  el.id = "app-config";
  el.type = "application/json";
  el.textContent = JSON.stringify({
    tenant: { schema_name: "dev", user_email: "dev@example.com", user_id: "1" },
    api: {
      base_url: "/api/v1",
      langflow_auto_login_url: "/api/v1/langflow/auth/auto-login",
      langflow_base_url: "http://localhost:7860",
    },
    csrf_token: "dev-csrf-token",
  });
  document.head.appendChild(el);
}

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

Create `/home/RID/frontend/apps/rockitdown/src/App.tsx`:
```tsx
import { useEffect, useState } from "react";
import { readAppConfig, type AppConfig } from "@rid/shared";
import { useLangflowAuth } from "./hooks/useLangflowAuth";

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const { credentials, loading, error } = useLangflowAuth(config);

  useEffect(() => {
    try {
      setConfig(readAppConfig());
    } catch (e) {
      console.error("Failed to read app config:", e);
    }
  }, []);

  if (!config) return <div>Loading config...</div>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>RockItDown</h1>
      <p>Tenant: <strong>{config.tenant.schema_name}</strong></p>
      <p>User: <strong>{config.tenant.user_email}</strong></p>
      {loading && <p>Connecting to Langflow...</p>}
      {error && <p style={{ color: "red" }}>Langflow error: {error}</p>}
      {credentials && (
        <p style={{ color: "green" }}>
          Langflow connected. API key: {credentials.api_key.slice(0, 8)}...
        </p>
      )}
    </div>
  );
}
```

Create `/home/RID/frontend/apps/rockitdown/src/hooks/useLangflowAuth.ts`:
```typescript
import { useEffect, useState } from "react";
import type { AppConfig, LangflowCredentials } from "@rid/shared";

interface UseLangflowAuthResult {
  credentials: LangflowCredentials | null;
  loading: boolean;
  error: string | null;
}

/**
 * Fetches Langflow credentials via the Django/FastAPI auto-login bridge.
 *
 * Flow:
 *   1. Call GET /api/v1/langflow/auth/auto-login (Django session cookie is
 *      sent automatically by the browser).
 *   2. Store returned access_token and api_key in memory (not localStorage).
 *   3. Re-runs when config changes (i.e., once on mount).
 */
export function useLangflowAuth(config: AppConfig | null): UseLangflowAuthResult {
  const [credentials, setCredentials] = useState<LangflowCredentials | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!config) return;

    let cancelled = false;

    async function fetchCredentials() {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(config!.api.langflow_auto_login_url, {
          credentials: "include",
          headers: {
            "X-CSRFToken": config!.csrf_token,
          },
        });
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(`${resp.status}: ${text}`);
        }
        const data = (await resp.json()) as LangflowCredentials;
        if (!cancelled) setCredentials(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void fetchCredentials();
    return () => {
      cancelled = true;
    };
  }, [config]);

  return { credentials, loading, error };
}
```

**Verification:**
```bash
cd /home/RID/frontend
pnpm install
pnpm --filter @rid/rockitdown typecheck
# Expected: no TypeScript errors
```

---

### Task 4.4 — Build script: copy dist to Django

**Target:** frontend
**Working Directory:** `/home/RID/frontend/apps/rockitdown`
**Agent:** ring:frontend-engineer
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/frontend/apps/rockitdown/scripts/copy-to-django.js`

```javascript
#!/usr/bin/env node
/**
 * Post-build script: copies Vite dist output into Django's staticfiles
 * and templates directories so Django can serve the SPA.
 *
 * Source:      dist/
 * Destination:
 *   assets → /home/RID/backend/static/apps/rockitdown/assets/
 *   (index.html is served by Django template, NOT as a static file)
 *
 * Run automatically after `vite build` via the "build" npm script.
 */
import { cpSync, mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = resolve(__dirname, "../dist");
const backendStatic = resolve(__dirname, "../../../../backend/static/apps/rockitdown");

if (!existsSync(distDir)) {
  console.error("dist/ not found — run vite build first");
  process.exit(1);
}

mkdirSync(backendStatic, { recursive: true });

// Copy the assets folder (JS, CSS, images) into Django staticfiles
cpSync(resolve(distDir, "assets"), resolve(backendStatic, "assets"), { recursive: true });

console.log(`Copied assets → ${backendStatic}/assets`);
```

Update `/home/RID/frontend/apps/rockitdown/package.json` to use `"type": "module"` so the `.js` script can use ESM imports:

```json
{
  "name": "@rid/rockitdown",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build && node scripts/copy-to-django.js",
    "lint": "eslint src",
    "typecheck": "tsc --noEmit",
    "preview": "vite preview"
  },
  "dependencies": {
    "@rid/shared": "workspace:*",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }
}
```

**Verification:**
```bash
cd /home/RID/frontend
pnpm install
pnpm --filter @rid/rockitdown build 2>&1 | tail -10
# Expected: "Copied assets → .../backend/static/apps/rockitdown/assets"
ls /home/RID/backend/static/apps/rockitdown/assets/
# Expected: index.js  index.css
```

---

## Phase 5: Langflow Docker Integration

### Task 5.1 — docker-compose.yml for Langflow service

**Target:** shared
**Working Directory:** `/home/RID`
**Agent:** ring:devops-engineer
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/docker/docker-compose.yml`

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: rid
      POSTGRES_PASSWORD: rid
      POSTGRES_DB: rid
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rid"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  langflow:
    image: langflowai/langflow:latest
    restart: unless-stopped
    environment:
      LANGFLOW_DATABASE_URL: postgresql://rid:rid@postgres:5432/langflow
      LANGFLOW_SUPERUSER: admin
      LANGFLOW_SUPERUSER_PASSWORD: adminpassword
      LANGFLOW_SECRET_KEY: change-me-in-production-langflow-secret
      LANGFLOW_AUTO_LOGIN: "false"
    volumes:
      - langflow_data:/app/langflow
      - ./langflow-components:/app/langflow/components/custom
    ports:
      - "7860:7860"
    depends_on:
      postgres:
        condition: service_healthy

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - langflow

volumes:
  postgres_data:
  langflow_data:
```

**Verification:**
```bash
cd /home/RID/docker
docker compose config 2>&1 | head -5
# Expected: name: docker (or similar valid output — no YAML errors)
```

---

### Task 5.2 — Nginx reverse proxy configuration

**Target:** shared
**Working Directory:** `/home/RID/docker`
**Agent:** ring:devops-engineer
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/docker/nginx/nginx.conf`

```nginx
# /home/RID/docker/nginx/nginx.conf
#
# Routes:
#   /langflow/   → Langflow container (port 7860)
#   /api/        → Django/FastAPI backend (port 8000)
#   /            → Django/FastAPI backend (port 8000)

worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    upstream backend {
        server host.docker.internal:8000;
    }

    upstream langflow {
        server langflow:7860;
    }

    server {
        listen 80;
        server_name _;

        # ------------------------------------------------------------------
        # Langflow UI + API
        # Strips the /langflow prefix so Langflow receives paths it expects.
        # ------------------------------------------------------------------
        location /langflow/ {
            proxy_pass         http://langflow/;
            proxy_http_version 1.1;
            proxy_set_header   Upgrade $http_upgrade;
            proxy_set_header   Connection "upgrade";
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_buffering    off;
        }

        # ------------------------------------------------------------------
        # Django + FastAPI backend (everything else)
        # ------------------------------------------------------------------
        location / {
            proxy_pass         http://backend;
            proxy_http_version 1.1;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_read_timeout    120s;
        }
    }
}
```

**Verification:**
```bash
docker run --rm -v /home/RID/docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine nginx -t
# Expected: nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

### Task 5.3 — Custom Langflow components volume directory

**Target:** shared
**Working Directory:** `/home/RID/docker`
**Agent:** ring:devops-engineer
**Time estimate:** 1 min

**Instructions:**
```bash
mkdir -p /home/RID/docker/langflow-components
touch /home/RID/docker/langflow-components/.gitkeep
```

**Verification:**
```bash
ls /home/RID/docker/langflow-components/
# Expected: .gitkeep
```

---

## Phase 6: Auth + Multi-Tenancy Wiring

### Task 6.1 — Allauth configuration

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/apps/accounts/adapters.py`

This file customises allauth's signup flow to auto-create a `TenantUser` profile on registration.

```python
"""
Custom allauth adapter.

Overrides save_user to create a TenantUser profile immediately after
the Django User is saved, ensuring the profile always exists.
"""
from __future__ import annotations

from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()


class RIDAccountAdapter(DefaultAccountAdapter):
    def save_user(
        self,
        request: HttpRequest,
        user: "User",  # type: ignore[override]
        form: object,
        commit: bool = True,
    ) -> "User":
        user = super().save_user(request, user, form, commit=commit)
        if commit:
            from apps.accounts.models import TenantUser
            TenantUser.objects.get_or_create(user=user)
        return user
```

Add to `/home/RID/backend/core/settings.py` (append at the bottom):
```python
# Custom allauth adapter — creates TenantUser on signup
ACCOUNT_ADAPTER = "apps.accounts.adapters.RIDAccountAdapter"
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from allauth.account.adapter import get_adapter
from django.test import RequestFactory
adapter = get_adapter()
print('adapter class:', type(adapter).__name__)
"
# Expected: adapter class: RIDAccountAdapter
```

---

### Task 6.2 — Tenant creation signal → create Langflow workspace

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Files to Create:**
- `/home/RID/backend/apps/tenants/signals.py`
- `/home/RID/backend/apps/tenants/apps.py` (update)

Create `/home/RID/backend/apps/tenants/signals.py`:
```python
"""
Signal handlers for the tenants app.

post_save on Customer triggers Langflow workspace creation.
We use post_save with created=True so the schema already exists
(TenantMixin.save() creates the schema before post_save fires).
"""
from __future__ import annotations

import asyncio
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="tenants.Customer")
def on_customer_created(
    sender: type,
    instance: object,
    created: bool,
    **kwargs: object,
) -> None:
    """
    When a new Customer tenant is created, provision a Langflow workspace.

    Langflow does not have a first-class "workspace" concept in all versions.
    Here we create the superuser admin's folder in Langflow tagged with the
    tenant schema name so flows are isolated per tenant.

    This is a fire-and-forget async call via asyncio.  If Langflow is not
    yet running the error is logged but does not fail tenant creation.
    """
    if not created:
        return

    schema: str = getattr(instance, "schema_name", "")
    if schema == "public":
        return

    logger.info("New tenant created: %s — provisioning Langflow workspace", schema)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_provision_langflow_workspace(schema))
        else:
            asyncio.run(_provision_langflow_workspace(schema))
    except RuntimeError:
        # No event loop in sync context (e.g. management commands)
        import threading
        threading.Thread(
            target=asyncio.run,
            args=(_provision_langflow_workspace(schema),),
            daemon=True,
        ).start()


async def _provision_langflow_workspace(schema_name: str) -> None:
    """
    Create a Langflow folder named after the tenant schema.

    Langflow REST endpoint: POST /api/v1/folders/
    """
    import httpx
    from django.conf import settings

    try:
        async with httpx.AsyncClient(
            base_url=settings.LANGFLOW_BASE_URL, timeout=15
        ) as client:
            # Authenticate as superuser
            login_resp = await client.post(
                "/api/v1/login",
                data={
                    "username": settings.LANGFLOW_SUPERUSER,
                    "password": settings.LANGFLOW_SUPERUSER_PASSWORD,
                },
            )
            if login_resp.status_code != 200:
                logger.error(
                    "Langflow superuser login failed for tenant %s: %s",
                    schema_name,
                    login_resp.text,
                )
                return

            token = login_resp.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            folder_resp = await client.post(
                "/api/v1/folders/",
                json={"name": schema_name, "description": f"Workspace for tenant {schema_name}"},
                headers=headers,
            )
            if folder_resp.status_code in (200, 201):
                logger.info("Langflow workspace created for tenant: %s", schema_name)
            else:
                logger.warning(
                    "Langflow workspace creation returned %s for tenant %s: %s",
                    folder_resp.status_code,
                    schema_name,
                    folder_resp.text,
                )
    except Exception as exc:
        logger.error("Failed to provision Langflow workspace for %s: %s", schema_name, exc)
```

Update `/home/RID/backend/apps/tenants/apps.py`:
```python
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    label = "tenants"

    def ready(self) -> None:
        import apps.tenants.signals  # noqa: F401  registers signal handlers
```

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from django.db.models.signals import post_save
from apps.tenants.models import Customer
receivers = post_save.receivers
print('post_save receivers registered:', len(receivers))
"
# Expected: post_save receivers registered: 1 (or more)
```

---

### Task 6.3 — Stripe billing stubs

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Files to Create:**
- `/home/RID/backend/apps/billing/__init__.py`
- `/home/RID/backend/apps/billing/apps.py`
- `/home/RID/backend/apps/billing/models.py`
- `/home/RID/backend/apps/billing/views.py`

Create `/home/RID/backend/apps/billing/__init__.py` (empty).

Create `/home/RID/backend/apps/billing/apps.py`:
```python
from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    label = "billing"
```

Create `/home/RID/backend/apps/billing/models.py`:
```python
"""
Billing models — Stripe subscription data per tenant.

Stored in the shared schema so billing records are visible from the
public schema and any admin tooling.
"""
from __future__ import annotations

from django.db import models


class Subscription(models.Model):
    """Maps a django-tenants Customer to a Stripe subscription."""

    PLAN_FREE = "free"
    PLAN_STARTER = "starter"
    PLAN_PRO = "pro"
    PLAN_ENTERPRISE = "enterprise"

    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_STARTER, "Starter"),
        (PLAN_PRO, "Pro"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]

    schema_name = models.CharField(max_length=63, unique=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    plan = models.CharField(max_length=32, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active = models.BooleanField(default=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "billing"

    def __str__(self) -> str:
        return f"Subscription({self.schema_name}, {self.plan})"
```

Create `/home/RID/backend/apps/billing/views.py`:
```python
"""
Stripe webhook handler.

POST /billing/webhook/
  Verifies Stripe signature.
  Updates Subscription model on relevant events.
"""
from __future__ import annotations

import json
import logging

import stripe
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except stripe.error.SignatureVerificationError as e:
            logger.warning("Invalid Stripe signature: %s", e)
            return HttpResponse(status=400)

        event_type: str = event.get("type", "")
        logger.info("Stripe event received: %s", event_type)

        if event_type == "customer.subscription.updated":
            self._handle_subscription_updated(event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event["data"]["object"])

        return JsonResponse({"received": True})

    def _handle_subscription_updated(self, subscription: dict) -> None:
        from apps.billing.models import Subscription
        stripe_sub_id: str = subscription.get("id", "")
        try:
            sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
            sub.is_active = subscription.get("status") == "active"
            sub.save(update_fields=["is_active", "updated_at"])
        except Subscription.DoesNotExist:
            logger.warning("Subscription not found for stripe id: %s", stripe_sub_id)

    def _handle_subscription_deleted(self, subscription: dict) -> None:
        from apps.billing.models import Subscription
        stripe_sub_id: str = subscription.get("id", "")
        try:
            sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
            sub.is_active = False
            sub.save(update_fields=["is_active", "updated_at"])
        except Subscription.DoesNotExist:
            logger.warning("Subscription not found for stripe id: %s", stripe_sub_id)
```

Add billing URL to `/home/RID/backend/core/urls.py`:
```python
from apps.billing.views import StripeWebhookView
# inside urlpatterns:
path("billing/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
```

Add `"apps.billing"` to `SHARED_APPS` in `/home/RID/backend/core/settings.py`.

**Verification:**
```bash
cd /home/RID/backend
uv run python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.billing.models import Subscription
print('Subscription model:', Subscription)
"
# Expected: Subscription model: <class 'apps.billing.models.Subscription'>
```

---

## Phase 7: Server Entry Point + Developer Tooling

### Task 7.1 — Uvicorn entrypoint and Makefile

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 2 min

**Files to Create:**
- `/home/RID/backend/run.py`
- `/home/RID/Makefile`

Create `/home/RID/backend/run.py`:
```python
"""
Development server entrypoint.

Runs Uvicorn with hot-reload.  In production, run:
  uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --workers 4
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "core.asgi:application",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["core", "apps", "api"],
        log_level="info",
    )
```

Create `/home/RID/Makefile`:
```makefile
.PHONY: backend frontend docker-up docker-down migrate shell

# ── Backend ──────────────────────────────────────────────────────────────────
backend:
	cd backend && uv run python run.py

migrate:
	cd backend && uv run python manage.py migrate_schemas --shared

makemigrations:
	cd backend && uv run python manage.py makemigrations $(app)

shell:
	cd backend && uv run python manage.py shell

test-backend:
	cd backend && uv run pytest

# ── Frontend ─────────────────────────────────────────────────────────────────
frontend:
	cd frontend && pnpm dev:rockitdown

build-frontend:
	cd frontend && pnpm build:all

# ── Docker ───────────────────────────────────────────────────────────────────
docker-up:
	cd docker && docker compose up -d

docker-down:
	cd docker && docker compose down

docker-logs:
	cd docker && docker compose logs -f

# ── Combined dev ─────────────────────────────────────────────────────────────
dev: docker-up
	@echo "Starting backend and frontend..."
	$(MAKE) -j2 backend frontend
```

**Verification:**
```bash
cd /home/RID
make --version | head -1
# Expected: GNU Make ...
cat Makefile | grep "^backend:"
# Expected: backend:
```

---

### Task 7.2 — pytest configuration

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 2 min

**Files to Create:**
- `/home/RID/backend/pytest.ini`
- `/home/RID/backend/tests/__init__.py`
- `/home/RID/backend/tests/test_health.py`

Create `/home/RID/backend/pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

Create `/home/RID/backend/tests/__init__.py` (empty).

Create `/home/RID/backend/tests/test_health.py`:
```python
"""
Smoke test: FastAPI /api/health endpoint responds with {"status": "ok"}.

Uses httpx.AsyncClient with the ASGI app directly — no network required.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django
    django.setup()

    from api.main import create_app
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Add `anyio` and `pytest-asyncio` to dev dependencies:
```bash
cd /home/RID/backend
uv add --dev pytest-asyncio anyio
```

**Verification:**
```bash
cd /home/RID/backend
uv run pytest tests/test_health.py -v
# Expected:
# tests/test_health.py::test_health_endpoint PASSED
```

---

## Execution Order

```
Phase 1:  1.1 → 1.2 → 1.3 → 1.4 → 1.5   (backend foundation)
Phase 2:  2.1 → 2.2 → 2.3                  (FastAPI layer)
Phase 3:  3.1 → 3.2 → 3.3 → 3.4           (Django templates)
Phase 4:  4.1 → 4.2 → 4.3 → 4.4           (frontend monorepo)
Phase 5:  5.1 → 5.2 → 5.3                  (Docker + Nginx)
Phase 6:  6.1 → 6.2 → 6.3                  (auth + tenancy wiring)
Phase 7:  7.1 → 7.2                         (dev tooling)
```

Phases 4 and 5 are independent of each other and can run in parallel with Phase 3.

---

## Full Dependency Tree

```
pyproject.toml deps needed before any Phase 1 task:
  django-tenants, django-allauth[socialaccount], redis, httpx, stripe

Phase 1.5 (migrations) requires:
  - PostgreSQL running (use docker compose up postgres)
  - All Phase 1.1–1.4 tasks complete

Phase 2.2 (langflow_auth router) requires:
  - Phase 3.2 complete (TenantUser model)

Phase 4.4 (copy-to-django build script) requires:
  - Phase 4.3 complete (Vite build configured)
  - /home/RID/backend/static/ directory exists (created by Django collectstatic)

Phase 6.2 (tenant signal) requires:
  - Phase 2.2 complete (langflow_client service)

Phase 7.2 (pytest health test) requires:
  - Phase 2.1 complete (FastAPI app factory)
```

---

## Post-Plan Checklist

After all phases are complete, run these end-to-end checks:

```bash
# 1. Start infrastructure
cd /home/RID/docker && docker compose up -d

# 2. Run migrations
cd /home/RID/backend && uv run python manage.py migrate_schemas --shared

# 3. Create a superuser for local testing
cd /home/RID/backend && uv run python manage.py createsuperuser --schema=public

# 4. Build frontend and copy to Django
cd /home/RID/frontend && pnpm build:all

# 5. Collect staticfiles
cd /home/RID/backend && uv run python manage.py collectstatic --noinput

# 6. Start the backend
cd /home/RID/backend && uv run python run.py

# 7. Verify API health
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}

# 8. Verify Django admin
curl -I http://localhost:8000/admin/
# Expected: HTTP 302 → /admin/login/

# 9. Verify SPA redirect
curl -I http://localhost:8000/
# Expected: HTTP 302 → /app/

# 10. Run all backend tests
cd /home/RID/backend && uv run pytest
# Expected: all tests PASSED
```
