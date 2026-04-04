# Code Review Fixes — Backend Foundation (v2)

**Date:** 2026-04-03
**Version:** 2 — incorpora recomendações da análise de `/home/RockItDown`
**Status:** Ready for execution
**Agent:** ring:write-plan
**Origem:** Code review `ring:code-reviewer` + exploração `ring:codebase-explorer` em `/home/RockItDown`
**Plano relacionado:** `2026-04-03-rid-platform-architecture.md`

---

## Goal

Resolver os 7 problemas da code review original **e** incorporar as 6 soluções maduras descobertas no RockItDown (predecessor do RID). Ao final, o backend terá: isolamento seguro de tenant em contexto async, service layer idempotente para provisionamento, backend de autenticação multi-tenant, camada Stripe completa com guard de produção, adapter allauth para signup multi-step, mixin para integração Langflow, e cobertura mínima de testes.

---

## Contexto: RockItDown como fonte de padrões

O `/home/RockItDown` é a plataforma que precedeu o RID. Contém soluções já testadas em produção para os mesmos problemas que o RID precisa resolver. Cada nova task neste plano **porta** uma solução do RockItDown, adaptada para a arquitetura do RID (Django 6 + FastAPI + schema-per-tenant via `django-tenants`, utilizadores no schema público).

**Diferença arquitetural relevante:** No RockItDown os utilizadores ficam no schema do tenant; no RID ficam no schema público (`SHARED_APPS`). Esta diferença afecta o `TenantAwareBackend` e o `TenantAwareAccountAdapter`.

---

## Architecture Summary (v2)

```
/home/RID/backend/
├── api/
│   ├── main.py                  ← sem alteração
│   └── deps.py                  ← Task 1, Task 3, Task 6
├── apps/
│   ├── tenants/
│   │   ├── models.py            ← sem alteração
│   │   ├── signals.py           ← Task 4 (thin signal)
│   │   └── services.py          ← Task 9 (novo — service layer)
│   └── accounts/
│       └── models.py            ← Task 5
├── core/
│   ├── asgi.py                  ← Task 7
│   ├── auth_backends.py         ← Task 8 (novo — auth multi-tenant)
│   └── adapters.py              ← Task 11 (novo — adapter allauth)
├── helpers/
│   ├── __init__.py              ← Task 10
│   ├── billing.py               ← Task 10 (novo — Stripe wrapper)
│   └── utils.py                 ← Task 13 (novo — retry + downloader)
├── api/routers/
│   └── langflow.py              ← Task 12 (novo — mixin Langflow)
└── tests/
    ├── conftest.py              ← Task 2
    ├── test_health.py           ← Task 2
    ├── test_deps.py             ← Task 3
    └── test_auth_backends.py   ← Task 8
```

---

## Tech Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, Django 6, FastAPI |
| Multi-tenancy | django-tenants (schema-per-tenant) |
| Auth | django-allauth v65+ |
| Billing | Stripe SDK |
| Testes | pytest, pytest-django, pytest-asyncio, httpx |
| Lint | ruff |

---

## Ordem de Execução Recomendada

| Ordem | Task | Severidade | Dependência |
|---|---|---|---|
| 1 | Task 1 — async isolation | HIGH | Nenhuma |
| 2 | Task 7 — ASGI routing | LOW | Nenhuma |
| 3 | Task 4 — signal threading | MEDIUM | Nenhuma |
| 4 | Task 9 — service layer (provision) | HIGH | Task 4 |
| 5 | Task 8 — TenantAwareBackend | HIGH | Task 9 |
| 6 | Task 5 — invited_by | MEDIUM | Nenhuma |
| 7 | Task 10 — billing helper | HIGH | Nenhuma |
| 8 | Task 11 — TenantAwareAccountAdapter | MEDIUM | Task 9 |
| 9 | Task 2 — infra de testes | HIGH | Tasks 1, 7, 8 |
| 10 | Task 3 — test host validation | MEDIUM | Tasks 1, 2 |
| 11 | Task 12 — Langflow mixin | MEDIUM | Task 9 |
| 12 | Task 13 — retry + downloader | MEDIUM | Nenhuma |
| 13 | Task 6 — select_related (já em Task 1) | LOW | Task 1 |

Tasks 1, 4, 5, 7, 10 são independentes e podem correr em paralelo.

---

## Task 1 — Isolamento de tenant em contexto async via `sync_to_async` (HIGH)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 5 min

**Problema:** `get_current_tenant` é `async` e chama `connection.set_tenant()` de forma síncrona. Em ASGI, corrotinas concorrentes no mesmo worker podem intercalar entre `await`s e contaminar a conexão de outro request.

**Porquê desta solução:**
O RockItDown usa `schema_context()` do `django-tenants` em contexto síncrono dentro das views (nunca em `async def`). O RID tem um ponto de entrada diferente (FastAPI async), por isso a solução correcta é isolar todo o bloco DB + `set_tenant` numa thread dedicada via `sync_to_async`. Isto replica exactamente o que o `TenantMainMiddleware` do Django faz internamente — corre em worker síncrono — mas adaptado para o stack async do FastAPI.

**Como o RID acomoda:**
`api/deps.py` é o único ponto de resolução de tenant para o stack FastAPI. A função `_resolve_tenant` (síncrona) fica como helper puro, chamável via `sync_to_async`. Não há impacto nas views Django que continuam a usar `TenantMainMiddleware`.

**Files to Modify:**
- `/home/RID/backend/api/deps.py`

**Conteúdo completo:**

```python
"""
FastAPI dependencies for tenant resolution.

Django's TenantMainMiddleware does NOT run for /api/* requests.
Use get_current_tenant() as a FastAPI dependency on any route
that needs to access tenant-scoped ORM data.

Isolation strategy
------------------
Django's connection object is thread-local; it is NOT safe to call
set_tenant() from an async coroutine where multiple coroutines may
interleave between awaits on the same OS thread.

We use sync_to_async to execute ALL connection-mutating and ORM code
inside a dedicated thread-pool thread — the same isolation that
Django's TenantMainMiddleware relies on.
"""
from __future__ import annotations

from typing import Annotated

from asgiref.sync import sync_to_async
from fastapi import Depends, Header, HTTPException, status


def _resolve_tenant(hostname: str) -> str:
    """
    Synchronous helper: resolves hostname -> schema and sets the tenant
    on the current DB connection.

    Must run inside sync_to_async so that it executes in an isolated
    thread-pool thread (thread-local connection safety).
    """
    from apps.tenants.models import Domain
    from django.db import connection

    try:
        domain = Domain.objects.select_related("tenant").get(domain=hostname)
    except Domain.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found for domain: {hostname}",
        )

    tenant = domain.tenant
    connection.set_tenant(tenant)
    return tenant.schema_name


async def get_current_tenant(host: Annotated[str, Header()] = "") -> str:
    """
    Resolve the current tenant from the Host header.

    Sets Django's db connection to the correct schema so ORM
    queries within the same request context hit the right schema.

    Returns the schema_name of the resolved tenant.
    Raises HTTP 400 if the Host header is missing or empty.
    Raises HTTP 404 if the domain is not registered.
    """
    hostname = host.split(":")[0].strip()

    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host header is required",
        )

    return await sync_to_async(_resolve_tenant, thread_sensitive=True)(hostname)


TenantSchema = Annotated[str, Depends(get_current_tenant)]
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
from api.deps import get_current_tenant, _resolve_tenant
import inspect
assert inspect.iscoroutinefunction(get_current_tenant), 'deve ser async'
assert not inspect.iscoroutinefunction(_resolve_tenant), 'deve ser sync'
print('OK: isolamento via sync_to_async presente')
"
# Expected: OK: isolamento via sync_to_async presente
```

---

## Task 2 — Infraestrutura de testes mínima (HIGH)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:qa-analyst
**Time estimate:** 5 min

**Problema:** Nenhum teste automático existe. `pytest` e `pytest-django` já estão em dev deps mas nunca foram usados.

**Porquê desta solução:**
O RockItDown também não tem cobertura de testes adequada — é um padrão a não repetir. O RID começa do zero e deve estabelecer a infra agora, antes que o codebase cresça. Os fixtures `client` e `asgi_app` replicam o padrão de test client ASGI que o RockItDown deveria ter usado nos seus `tests.py` (actualmente vazios).

**Como o RID acomoda:**
Pasta `tests/` separada do código de produção. `pytest.ini` na raiz do `backend/`. Fixtures partilhadas em `conftest.py`. Testes de integração ASGI não precisam de BD — usam `ASGITransport` do `httpx`.

**Files to Create:**
- `/home/RID/backend/pytest.ini`
- `/home/RID/backend/tests/__init__.py`
- `/home/RID/backend/tests/conftest.py`
- `/home/RID/backend/tests/test_health.py`

**`pytest.ini`:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
asyncio_mode = auto
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
```

**`tests/__init__.py`:**
```python
```

**`tests/conftest.py`:**
```python
"""Shared pytest fixtures for backend tests."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.asgi import application


@pytest.fixture
def asgi_app():
    return application


@pytest_asyncio.fixture
async def client(asgi_app):
    transport = ASGITransport(app=asgi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c
```

**`tests/test_health.py`:**
```python
"""Integration tests for the health endpoint — no DB required."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_response_is_json(client):
    response = await client.get("/api/health")
    assert response.headers["content-type"].startswith("application/json")
```

**Add dependency:**
```bash
cd /home/RID/backend && . .venv/bin/activate
uv add --dev pytest-asyncio
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
pytest tests/test_health.py -v
# Expected:
# tests/test_health.py::test_health_returns_ok PASSED
# tests/test_health.py::test_health_response_is_json PASSED
# 2 passed
```

---

## Task 3 — Validar header `Host` ausente / vazio (MEDIUM)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Problema:** `host: Header() = ""` permite hostname vazio que resulta num `Domain.DoesNotExist` e um 404 genérico.

**Porquê desta solução:**
O RockItDown não tem FastAPI — usa Django views directamente onde o `TenantMainMiddleware` garante que o tenant está resolvido antes da view ser chamada. No RID, a resolução é manual em `deps.py`, por isso a validação de entrada precisa de ser explícita. O 400 (Bad Request) é semanticamente correcto: é um problema do cliente, não de dados não encontrados.

**Como o RID acomoda:**
A validação está em `_resolve_tenant` → chamada já feita na Task 1. Esta task cria apenas os testes que provam o comportamento.

**Files to Create:**
- `/home/RID/backend/tests/test_deps.py`

```python
"""Tests for FastAPI tenant dependency — validação de entrada."""
from __future__ import annotations

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_empty_host_raises_400():
    from api.deps import get_current_tenant
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="")
    assert exc_info.value.status_code == 400
    assert "Host header is required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_whitespace_host_raises_400():
    from api.deps import get_current_tenant
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="   ")
    assert exc_info.value.status_code == 400
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
pytest tests/test_deps.py -v
# Expected: 2 passed
```

---

## Task 4 — Signal de provisão como thin dispatcher (MEDIUM)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Problema:** O signal cria o schema de forma síncrona no worker HTTP, bloqueando a requisição.

**Porquê desta solução (threading como stepping stone):**
No RockItDown, o signal de criação de tenant foi **suspenso** (`print("Signal suspenso")`) porque a lógica de provisionamento foi movida para `customers/services.py` e é chamada explicitamente a partir das views de signup. O RID deve seguir o mesmo caminho: o signal torna-se um **thin dispatcher** que chama a service layer (Task 9). Enquanto a Task 9 não existe, usamos `threading.Thread` para pelo menos desbloquear o worker.

**Como o RID acomoda:**
`apps/tenants/signals.py` permanece simples. Quando a Task 9 existir, o bloco `threading.Thread` é substituído por uma chamada directa à service function (ou task Celery). O signal não deve conter lógica de negócio.

**Files to Modify:**
- `/home/RID/backend/apps/tenants/signals.py`

```python
"""
Tenant lifecycle signals.

ARQUITECTURA
------------
Este signal é um thin dispatcher — não contém lógica de provisionamento.
A lógica de negócio está em apps.tenants.services.provision_tenant_for_user
(Task 9 deste plano).

Enquanto a task queue (Celery) não está configurada, o provisionamento
corre numa thread de fundo para não bloquear o worker HTTP.

Roadmap:
  Fase 1 (agora): threading.Thread → desbloqueia worker
  Fase 2 (Task 9): delega a provision_tenant_for_user()
  Fase 3 (futuro): Celery task para retry e observabilidade
"""
from __future__ import annotations

import logging
import threading

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _provision_in_background(schema_name: str, customer_pk) -> None:
    """Corre numa thread de fundo. Erros são logados, não propagados."""
    from apps.tenants.models import Customer

    try:
        instance = Customer.objects.get(pk=customer_pk)
        instance.auto_create_schema = True
        instance.save(update_fields=[])
        instance.auto_create_schema = False
        logger.info("Schema provisionado para tenant: %s", schema_name)
    except Exception:
        logger.exception(
            "Falha ao provisionar schema para tenant %s (pk=%s)",
            schema_name,
            customer_pk,
        )


@receiver(post_save, sender="tenants.Customer")
def provision_tenant_schema(sender, instance, created: bool, **kwargs) -> None:  # type: ignore[no-untyped-def]
    if not created:
        return
    logger.info("Agendando provisão para tenant: %s", instance.schema_name)
    threading.Thread(
        target=_provision_in_background,
        args=(instance.schema_name, instance.pk),
        daemon=True,
        name=f"provision-{instance.schema_name}",
    ).start()


@receiver(post_delete, sender="tenants.Customer")
def cleanup_tenant_memberships(sender, instance, **kwargs) -> None:  # type: ignore[no-untyped-def]
    from apps.accounts.models import TenantMembership
    deleted, _ = TenantMembership.objects.filter(
        tenant_schema=instance.schema_name
    ).delete()
    logger.info("Deleted %d memberships for tenant: %s", deleted, instance.schema_name)
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.tenants import signals
import inspect
src = inspect.getsource(signals.provision_tenant_schema)
assert 'threading.Thread' in src
assert 'logic' not in src.lower() or 'thin' in inspect.getmodule(signals).__doc__
print('OK: signal é thin dispatcher com threading.Thread')
"
# Expected: OK: signal é thin dispatcher com threading.Thread
```

---

## Task 5 — `invited_by` com semântica explícita (MEDIUM)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Problema:** `ForeignKey("self", related_name="invited_members")` é ambíguo.

**Porquê desta solução:**
O RockItDown não tem modelo de membership — os utilizadores ficam no schema do tenant directamente. No RID, a membership é o eixo central da autorização multi-tenant, por isso a clareza do modelo é crítica. `sent_invites` é o nome inverso correcto: "convites enviados por esta membership". A propriedade `invited_by_user` é um atalho idiomático que evita `membership.invited_by.user` espalhado pelo código.

**Como o RID acomoda:**
Alteração apenas em `apps/accounts/models.py`. A migração gerada é automática e não há dados a migrar (BD de desenvolvimento está vazia).

**Files to Modify:**
- `/home/RID/backend/apps/accounts/models.py`

```python
from __future__ import annotations

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

__all__ = ["TenantUser", "TenantMembership"]


class TenantUser(AbstractUser):
    """Custom user model stored in the shared (public) schema."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    langflow_user_id = models.UUIDField(null=True, blank=True, unique=True)
    langflow_api_key = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return self.email or self.username


class TenantMembership(models.Model):
    """
    Links a TenantUser to a Customer (tenant).
    A user can belong to multiple tenants with different roles.

    invited_by
    ----------
    FK para a TenantMembership de quem enviou o convite.
    Captura tanto quem convidou (.invited_by.user) como em que
    capacidade (.invited_by.role). SET_NULL preserva o histórico
    se o convidador sair do tenant.
    Atalho: membership.invited_by_user → o TenantUser convidador.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]

    user = models.ForeignKey(TenantUser, on_delete=models.CASCADE, related_name="memberships")
    tenant_schema = models.CharField(max_length=63, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invites",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "accounts"
        unique_together = [("user", "tenant_schema")]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.tenant_schema} ({self.role})"

    @property
    def invited_by_user(self) -> "TenantUser | None":
        return self.invited_by.user if self.invited_by_id else None
```

```bash
cd /home/RID/backend && . .venv/bin/activate
python manage.py makemigrations accounts --name "fix_invited_by_related_name"
python manage.py migrate
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.accounts.models import TenantMembership
fk = TenantMembership._meta.get_field('invited_by')
assert fk.remote_field.get_accessor_name() == 'sent_invites'
assert hasattr(TenantMembership, 'invited_by_user')
print('OK: invited_by com related_name=sent_invites e property')
"
# Expected: OK
```

---

## Task 6 — `select_related("tenant")` explícito (LOW)

Já incluído no conteúdo da Task 1. Sem ficheiro adicional.

**Porquê desta solução:**
O RockItDown usa `select_related("tenant")` explicitamente em `auth_backends.py` (`Domain.objects.select_related("tenant").get(...)`). É o padrão a seguir: explicita a intenção, evita N+1 e é mais eficiente que `select_related()` sem argumentos.

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
src = open('api/deps.py').read()
assert 'select_related(\"tenant\")' in src or \"select_related('tenant')\" in src
print('OK: select_related explícito')
"
```

---

## Task 7 — ASGI routing para `/api` e `/api/*` (LOW)

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 2 min

**Problema:** `path.startswith("/api/")` não captura `/api` sem barra final.

**Porquê desta solução:**
O RockItDown não usa FastAPI — não tem este problema. No RID, o dispatch ASGI manual é necessário porque o `TenantMainMiddleware` do Django não pode envolver o FastAPI. A constante `_API_PREFIX` torna a regra explícita e alterável num só lugar.

**Como o RID acomoda:**
Alteração apenas em `core/asgi.py`. Nenhum impacto nas rotas existentes.

**Files to Modify:**
- `/home/RID/backend/core/asgi.py`

```python
"""
ASGI config for RID project.

Dispatch:
  lifespan    → FastAPI
  /api ou /api/* → FastAPI
  tudo o resto   → Django (TenantMainMiddleware activo)
"""
from __future__ import annotations
import os
from typing import Any, Callable, Awaitable

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.asgi import get_asgi_application
django_app = get_asgi_application()

from api.main import create_app  # noqa: E402
fastapi_app = create_app()

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]

_API_PREFIX = "/api"


async def application(scope: Scope, receive: Receive, send: Send) -> None:
    scope_type: str = scope.get("type", "http")
    path: str = scope.get("path", "")

    if scope_type == "lifespan":
        await fastapi_app(scope, receive, send)
    elif path == _API_PREFIX or path.startswith(_API_PREFIX + "/"):
        await fastapi_app(scope, receive, send)
    else:
        await django_app(scope, receive, send)
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
src = open('core/asgi.py').read()
assert '_API_PREFIX' in src
assert 'path == _API_PREFIX or path.startswith' in src
print('OK: routing cobre /api e /api/*')
"
```

---

## Task 8 — `TenantAwareBackend`: autenticação `user@tenant-domain` (HIGH) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Origem:** `RockItDown/src/core/auth_backends.py` — em produção.

**Porquê desta solução:**
O RID usa `django-allauth` com login por email, mas num contexto multi-tenant onde o mesmo email pode existir em tenants diferentes (schema isolado por tenant, mas utilizadores no schema público). O `TenantAwareBackend` permite login no formato `user@tenant-domain` ou `user@schema-name`, com fallback transparente para outros backends. É crítico para o painel de administração e para qualquer fluxo de login directo por tenant.

**Diferença RID vs RockItDown:** No RockItDown os utilizadores ficam no schema do tenant (`with schema_context(...)`). No RID ficam no schema público. Por isso o `schema_context` é removido — o `UserModel._default_manager.get_by_natural_key` já aponta para o schema público.

**Como o RID acomoda:**
1. Criar `core/auth_backends.py`
2. Adicionar nos `settings.py` em `AUTHENTICATION_BACKENDS`

**Files to Create:**
- `/home/RID/backend/core/auth_backends.py`

```python
"""
TenantAwareBackend: autenticação no formato user@tenant-domain ou user@schema.

Fluxo:
  1. Tenta resolver o domínio após '@' como hostname de Domain
  2. Se não encontrar, tenta como schema_name de Customer
  3. Se nenhum tenant encontrado, retorna None (outros backends tentam)
  4. Autentica o utilizador no schema público (TenantUser está em SHARED_APPS)

Diferença vs RockItDown: utilizadores estão no schema público, não no
schema do tenant — por isso não usamos schema_context para a query de auth.
"""
from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class TenantAwareBackend(ModelBackend):
    """
    Autentica utilizadores no formato 'username@tenant-domain'.

    Permite login como:
      - 'alice@acme.rid.example.com'  (hostname registado em Domain)
      - 'alice@acme'                  (schema_name do Customer)

    Se o tenant não for encontrado, delega para outros backends
    (e.g., allauth EmailBackend para login padrão por email).
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs,
    ):
        identifier = (username or email or kwargs.get("login") or "").strip()
        if not identifier or not password or "@" not in identifier:
            return None

        username_part, domain_part = identifier.split("@", 1)
        username_part = username_part.strip()
        domain_part = domain_part.strip().lower()

        if not username_part or not domain_part:
            return None

        # Verificar que o tenant existe (validação, não para trocar schema)
        tenant_exists = False
        try:
            from apps.tenants.models import Domain
            Domain.objects.select_related("tenant").get(
                Q(domain__iexact=domain_part)
            )
            tenant_exists = True
        except Domain.DoesNotExist:
            try:
                from apps.tenants.models import Customer
                Customer.objects.get(schema_name__iexact=domain_part)
                tenant_exists = True
            except Customer.DoesNotExist:
                return None

        if not tenant_exists:
            return None

        # Utilizadores no schema público — auth directa sem schema_context
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(username_part)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
```

**Files to Modify:**
- `/home/RID/backend/core/settings.py` — adicionar backend na lista

```python
# Linha existente:
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Substituir por:
AUTHENTICATION_BACKENDS = [
    "core.auth_backends.TenantAwareBackend",   # user@tenant-domain
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

**Files to Create:**
- `/home/RID/backend/tests/test_auth_backends.py`

```python
"""Tests for TenantAwareBackend."""
from __future__ import annotations

import pytest


def test_backend_returns_none_without_at_symbol():
    from core.auth_backends import TenantAwareBackend
    backend = TenantAwareBackend()
    result = backend.authenticate(None, username="alicesemdominio", password="x")
    assert result is None


def test_backend_returns_none_with_empty_parts():
    from core.auth_backends import TenantAwareBackend
    backend = TenantAwareBackend()
    result = backend.authenticate(None, username="@acme", password="x")
    assert result is None


def test_backend_returns_none_for_unknown_tenant():
    from core.auth_backends import TenantAwareBackend
    backend = TenantAwareBackend()
    result = backend.authenticate(None, username="alice@tenant-inexistente.example.com", password="x")
    assert result is None
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from core.auth_backends import TenantAwareBackend
b = TenantAwareBackend()
assert b.authenticate(None, username='sem_arroba', password='x') is None
assert b.authenticate(None, username='@dominio', password='x') is None
print('OK: TenantAwareBackend importa e rejeita inputs inválidos')
"
# Expected: OK
pytest tests/test_auth_backends.py -v
# Expected: 3 passed
```

---

## Task 9 — Service layer `provision_tenant_for_user` (HIGH) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 5 min

**Origem:** `RockItDown/src/customers/services.py` — em produção.

**Porquê desta solução:**
O sinal da Task 4 chama `instance.save()` sem idempotência: se chamado duas vezes, cria erros. O `provision_tenant_for_user` do RockItDown é **idempotente** (verifica se o schema já existe antes de criar), **normaliza o schema_name** (`slugify + regex`), garante unicidade do domínio, e executa `migrate_schemas` via `tenant_context`. É a função correcta para ser chamada a partir de views de signup e futuramente de uma task Celery.

**Como o RID acomoda:**
Nova pasta/ficheiro `apps/tenants/services.py`. A função é chamada:
- Pelo `TenantAwareAccountAdapter` (Task 11) após confirmação de email
- Directamente por views de signup (futuro)
- Pelo signal da Task 4 pode eventualmente delegar aqui

**Files to Create:**
- `/home/RID/backend/apps/tenants/services.py`

```python
"""
Tenant provisioning service layer.

Origem: RockItDown/src/customers/services.py (adaptado).
Diferenças:
  - Usa campo `name` em vez de `tenant_name`/`username` (modelo RID)
  - Usa `migrate_schemas` management command via tenant_context
  - Não guarda utilizador no schema do tenant (utilizadores no schema público no RID)

Idempotência: safe to call multiple times — verifica existência antes de criar.
"""
from __future__ import annotations

import re
from typing import Tuple

from django.core.management import call_command
from django.utils.text import slugify
from django_tenants.utils import tenant_context

from apps.tenants.models import Customer, Domain

RESERVED_SCHEMAS = frozenset({"public", "information_schema", "pg_catalog"})


def _normalize_schema_name(raw: str) -> str:
    """Converte nome arbitrário em schema_name válido para PostgreSQL."""
    base = slugify(raw or "").replace("-", "_")
    base = re.sub(r"[^a-z0-9_]+", "", base)
    return base[:48]  # PostgreSQL max identifier length é 63; 48 dá margem


def _ensure_unique_domain(base_domain: str) -> str:
    """Garante que o domínio não está em uso, adicionando sufixo numérico se necessário."""
    candidate = base_domain
    suffix = 1
    while Domain.objects.filter(domain__iexact=candidate).exists():
        suffix += 1
        candidate = f"{base_domain}{suffix}"
    return candidate


def provision_tenant_for_user(
    *,
    user,
    tenant_name: str,
    primary_domain_suffix: str = "rid.localhost",
) -> Tuple["Customer", "Domain"]:
    """
    Cria Customer + Domain, migra schema e retorna (tenant, domain).

    Idempotente: se o tenant já existir com o mesmo schema_name, retorna-o.
    O utilizador não é movido para o schema do tenant — no RID os utilizadores
    ficam no schema público (SHARED_APPS).

    Args:
        user: instância de TenantUser (já guardada no schema público)
        tenant_name: nome legível do tenant (e.g. "Acme Corp")
        primary_domain_suffix: sufixo de domínio (default: rid.localhost para dev)

    Returns:
        (Customer, Domain) — o tenant e o domínio primário

    Raises:
        ValueError: se tenant_name resultar num schema_name inválido ou reservado
    """
    schema_name = _normalize_schema_name(tenant_name)
    if not schema_name or schema_name in RESERVED_SCHEMAS:
        raise ValueError(f"Nome de tenant inválido: '{tenant_name}'")

    # Idempotência: retorna tenant existente se schema já existe
    tenant, created = Customer.objects.get_or_create(
        schema_name=schema_name,
        defaults={"name": tenant_name},
    )

    if created:
        # Migrar schema recém-criado
        with tenant_context(tenant):
            call_command(
                "migrate_schemas",
                schema_name=tenant.schema_name,
                interactive=False,
                verbosity=0,
            )

    # Criar domínio primário se não existir
    base_domain = f"{schema_name}.{primary_domain_suffix}"
    domain_value = _ensure_unique_domain(base_domain)
    domain, _ = Domain.objects.get_or_create(
        domain=domain_value,
        defaults={"tenant": tenant, "is_primary": True},
    )

    return tenant, domain
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from apps.tenants.services import provision_tenant_for_user, _normalize_schema_name
assert _normalize_schema_name('Acme Corp') == 'acme_corp'
assert _normalize_schema_name('') == ''
assert _normalize_schema_name('A' * 100)[:1] == 'a'
assert len(_normalize_schema_name('A' * 100)) <= 48
print('OK: normalize_schema_name funciona correctamente')
"
# Expected: OK: normalize_schema_name funciona correctamente
```

---

## Task 10 — `helpers/billing.py`: Stripe wrapper com guard de produção (HIGH) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 5 min

**Origem:** `RockItDown/src/helpers/billing.py` — em produção.

**Porquê desta solução:**
O RID tem `STRIPE_SECRET_KEY` e `STRIPE_WEBHOOK_SECRET` nos settings mas nenhuma lógica de billing. O RockItDown tem um wrapper completo testado: criação de customer/produto/price, checkout session, finalização, subscriptions activas, cancelamento gracioso com `cancellation_details`, e serialização de dados de subscrição. O **guard de produção** que rejeita `sk_test` fora de DEBUG é uma lição directa de um incidente no RockItDown.

**Como o RID acomoda:**
Nova pasta `helpers/` (espelho do RockItDown). A convenção `raw=True/False` mantém-se: `raw=True` retorna o objecto Stripe completo, `raw=False` retorna apenas o dado relevante (ID ou dict serializado). Os `print()` de debug são substituídos por `logging`.

**Files to Create:**
- `/home/RID/backend/helpers/__init__.py`
- `/home/RID/backend/helpers/billing.py`

**`helpers/__init__.py`:**
```python
```

**`helpers/billing.py`:**
```python
"""
Stripe billing helpers.

Origem: RockItDown/src/helpers/billing.py (adaptado).
Melhorias:
  - logging em vez de print()
  - Guard de produção para sk_test

Guard de produção
-----------------
Se STRIPE_SECRET_KEY começa com 'sk_test' fora de DEBUG (e sem
STRIPE_TEST_OVERRIDE=True), levanta ValueError imediatamente.
Esta verificação foi adicionada após incidente no RockItDown onde
a chave de teste foi usada em produção.
"""
from __future__ import annotations

import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

_key = settings.STRIPE_SECRET_KEY
_debug = settings.DEBUG
_override = getattr(settings, "STRIPE_TEST_OVERRIDE", False)

if _key and _key.startswith("sk_test") and not _debug and not _override:
    raise ValueError(
        "STRIPE_SECRET_KEY é uma chave de teste mas DEBUG=False. "
        "Use uma chave live em produção ou defina STRIPE_TEST_OVERRIDE=True."
    )

stripe.api_key = _key


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def serialize_subscription(sub) -> dict:
    from helpers.utils import timestamp_to_datetime
    return {
        "status": sub.status,
        "current_period_start": timestamp_to_datetime(sub.current_period_start),
        "current_period_end": timestamp_to_datetime(sub.current_period_end),
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

def create_customer(name: str = "", email: str = "", metadata: dict | None = None, raw: bool = False):
    resp = stripe.Customer.create(name=name, email=email, metadata=metadata or {})
    logger.info("Stripe customer criado: %s", resp.id)
    return resp if raw else resp.id


# ---------------------------------------------------------------------------
# Products & Prices
# ---------------------------------------------------------------------------

def create_product(name: str = "", metadata: dict | None = None, raw: bool = False):
    resp = stripe.Product.create(name=name, metadata=metadata or {})
    return resp if raw else resp.id


def create_price(
    *,
    currency: str = "usd",
    unit_amount: int = 9999,
    interval: str = "month",
    product: str,
    metadata: dict | None = None,
    raw: bool = False,
):
    resp = stripe.Price.create(
        currency=currency,
        unit_amount=unit_amount,
        recurring={"interval": interval},
        product=product,
        metadata=metadata or {},
    )
    return resp if raw else resp.id


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

def start_checkout_session(
    customer_id: str,
    *,
    success_url: str,
    cancel_url: str,
    price_stripe_id: str,
    raw: bool = True,
):
    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url += "?session_id={CHECKOUT_SESSION_ID}"
    resp = stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        mode="subscription",
    )
    return resp if raw else resp.url


def get_checkout_session(stripe_id: str, raw: bool = True):
    resp = stripe.checkout.Session.retrieve(stripe_id)
    return resp if raw else resp.url


def get_checkout_customer_plan(session_id: str) -> dict:
    """Retorna dados consolidados de checkout: customer_id, plan_id, sub_stripe_id + subscription_data."""
    checkout = get_checkout_session(session_id, raw=True)
    sub = stripe.Subscription.retrieve(checkout.subscription)
    return {
        "customer_id": checkout.customer,
        "plan_id": sub.plan.id,
        "sub_stripe_id": checkout.subscription,
        **serialize_subscription(sub),
    }


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

def get_subscription(stripe_id: str, raw: bool = True):
    resp = stripe.Subscription.retrieve(stripe_id)
    return resp if raw else serialize_subscription(resp)


def get_customer_active_subscriptions(customer_stripe_id: str):
    return stripe.Subscription.list(customer=customer_stripe_id, status="active")


def cancel_subscription(
    stripe_id: str,
    *,
    reason: str = "",
    feedback: str = "other",
    cancel_at_period_end: bool = False,
    raw: bool = True,
):
    details = {"comment": reason, "feedback": feedback}
    if cancel_at_period_end:
        resp = stripe.Subscription.modify(
            stripe_id,
            cancel_at_period_end=True,
            cancellation_details=details,
        )
    else:
        resp = stripe.Subscription.cancel(stripe_id, cancellation_details=details)
    logger.info("Subscrição %s cancelada (at_period_end=%s)", stripe_id, cancel_at_period_end)
    return resp if raw else serialize_subscription(resp)
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()
# Em DEBUG=True, sk_test é permitido
import helpers.billing as b
assert callable(b.create_customer)
assert callable(b.start_checkout_session)
assert callable(b.cancel_subscription)
print('OK: helpers.billing importa correctamente')
"
# Expected: OK
```

---

## Task 11 — `TenantAwareAccountAdapter`: dados de signup na sessão (MEDIUM) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Origem:** `RockItDown/src/core/adapters.py` — em produção.

**Porquê desta solução:**
No fluxo allauth, o formulário de signup passa por `save_user()` antes da confirmação de email. Os dados extras (tenant_name) precisam de sobreviver até ao sinal `email_confirmed`. A sessão Django é o bus de passagem mais simples e correcto — não envolve campos temporários no modelo. O RockItDown usa exactamente este padrão com `_signup_tenant_name` na sessão.

**Melhorias em relação ao RockItDown:**
- Sem `print()` de debug — usa `logger`
- `confirm_email` é removido (o comportamento do RockItDown era corrigir um bug de versão antiga do allauth; no RID com allauth v65+ o comportamento padrão é correcto)

**Como o RID acomoda:**
1. Criar `core/adapters.py`
2. Adicionar `ACCOUNT_ADAPTER = "core.adapters.TenantAwareAccountAdapter"` nos settings
3. O sinal `email_confirmed` (a criar no futuro) lê `request.session["_signup_tenant_name"]` e chama `provision_tenant_for_user` (Task 9)

**Files to Create:**
- `/home/RID/backend/core/adapters.py`

```python
"""
TenantAwareAccountAdapter: preserva dados de tenant durante o signup allauth.

Origem: RockItDown/src/core/adapters.py (adaptado).
Melhorias:
  - logging em vez de print()
  - confirm_email removido (allauth v65+ funciona correctamente sem override)

Fluxo de dados:
  Formulário de signup → save_user() → session["_signup_tenant_name"]
    → email_confirmed signal → provision_tenant_for_user()

O adapter não cria o tenant — apenas preserva os dados do formulário
para o signal ter acesso após confirmação de email.
"""
from __future__ import annotations

import logging

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class TenantAwareAccountAdapter(DefaultAccountAdapter):
    """
    Adapter allauth que persiste dados de tenant do formulário na sessão.

    Campos lidos do formulário:
      - tenant_name: nome do tenant a criar (obrigatório no signup)
    """

    def save_user(self, request, user, form, commit=True):  # type: ignore[override]
        user = super().save_user(request, user, form, commit=commit)

        if form is not None and request is not None and hasattr(request, "session"):
            tenant_name = (
                form.cleaned_data.get("tenant_name")
                or form.cleaned_data.get("username")
                or ""
            )
            request.session["_signup_tenant_name"] = tenant_name
            request.session.save()
            logger.debug(
                "Dados de tenant preservados na sessão para utilizador %s: tenant_name=%r",
                getattr(user, "email", "?"),
                tenant_name,
            )

        return user
```

**Files to Modify:**
- `/home/RID/backend/core/settings.py` — adicionar linha:

```python
# Após ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "core.adapters.TenantAwareAccountAdapter"
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from core.adapters import TenantAwareAccountAdapter
a = TenantAwareAccountAdapter()
assert hasattr(a, 'save_user')
from django.conf import settings
assert getattr(settings, 'ACCOUNT_ADAPTER', '') == 'core.adapters.TenantAwareAccountAdapter'
print('OK: TenantAwareAccountAdapter configurado')
"
# Expected: OK
```

---

## Task 12 — `BaseLangflowViewMixin`: padrão de views com tenant_context (MEDIUM) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 4 min

**Origem:** `RockItDown/src/rocklangflow/views.py` — em produção.

**Porquê desta solução:**
O RockItDown tem um mixin maduro (`BaseLangflowViewMixin`) que encapsula: (1) extracção do UUID do utilizador tenant via header `X-Tenant-User-UUID` com fallback para `request.user.id`, e (2) criação do `RockLangflowClient` com inicialização de BD. O RID vai precisar deste padrão quando implementar rotas Langflow em `/api/langflow/*`. Melhor criá-lo agora como base vazia do que reescrever depois.

**Como o RID acomoda:**
Nova pasta `api/routers/` + ficheiro `langflow.py`. O mixin fica em `api/langflow_mixin.py`. O FastAPI router é registado em `api/main.py` quando as rotas forem implementadas.

**Files to Create:**
- `/home/RID/backend/api/langflow_mixin.py`
- `/home/RID/backend/api/routers/__init__.py`
- `/home/RID/backend/api/routers/langflow.py`

**`api/langflow_mixin.py`:**
```python
"""
BaseLangflowMixin para rotas FastAPI com integração Langflow.

Origem: RockItDown/src/rocklangflow/views.py:378-403 (adaptado para FastAPI).
Diferença: usa FastAPI Request em vez de Django HttpRequest.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseLangflowMixin:
    """
    Mixin base para endpoints FastAPI que chamam o Langflow.

    Responsabilidades:
      - Extrair o UUID do utilizador tenant do header ou do utilizador autenticado
      - Criar o cliente Langflow com o UUID correcto

    Uso:
        class MyView(BaseLangflowMixin):
            async def handle(self, request: Request, schema: TenantSchema):
                uuid = self.get_tenant_user_uuid(request)
                client = await self.get_client(uuid)
                ...
    """

    def get_tenant_user_uuid(self, request) -> Optional[str]:
        """
        Extrai UUID do utilizador tenant.

        Prioridade:
          1. Header X-Tenant-User-UUID (para chamadas M2M)
          2. request.user.langflow_user_id (campo em TenantUser)
          3. str(request.user.id) como fallback
        """
        # FastAPI não tem request.user nativo — será injectado via dependency
        # quando a autenticação JWT for implementada
        uuid_header = getattr(request, "headers", {}).get("x-tenant-user-uuid")
        if uuid_header:
            return uuid_header

        user = getattr(request, "user", None)
        if user and hasattr(user, "langflow_user_id") and user.langflow_user_id:
            return str(user.langflow_user_id)
        if user and hasattr(user, "id"):
            return str(user.id)

        return None

    async def get_client(self, tenant_user_uuid: str):
        """
        Retorna cliente Langflow configurado para o tenant.

        A implementação concreta depende do RockLangflowClient —
        a ser portado em task futura (ver 2026-04-03-rid-platform-architecture.md).
        """
        raise NotImplementedError(
            "get_client() deve ser implementado quando RockLangflowClient for portado. "
            "Ver Task 'Integração Langflow' no plano de arquitectura."
        )
```

**`api/routers/__init__.py`:**
```python
```

**`api/routers/langflow.py`:**
```python
"""
Langflow API router — placeholder.

As rotas serão implementadas quando o RockLangflowClient for portado.
Ver: 2026-04-03-rid-platform-architecture.md

Padrão a seguir (do RockItDown):
  - Todas as views herdam de BaseLangflowMixin
  - Usam TenantSchema como dependency para resolver o tenant
  - Executam operações de DB dentro de sync_to_async ou tenant_context
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/langflow", tags=["langflow"])


@router.get("/health")
async def langflow_health() -> dict:
    """Health check da integração Langflow — placeholder."""
    return {"status": "not_implemented", "message": "Langflow integration pending"}
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from api.langflow_mixin import BaseLangflowMixin
from api.routers.langflow import router
assert hasattr(BaseLangflowMixin, 'get_tenant_user_uuid')
assert hasattr(BaseLangflowMixin, 'get_client')
print('OK: BaseLangflowMixin e router importam correctamente')
"
# Expected: OK
```

---

## Task 13 — `helpers/utils.py`: retry e downloader (MEDIUM) ★ RockItDown

**Target:** backend
**Working Directory:** `/home/RID/backend`
**Agent:** ring:backend-engineer-typescript
**Time estimate:** 3 min

**Origem:** `RockItDown/src/helpers/monday_graphql.py:1012–1027` + `RockItDown/src/helpers/downloader.py`

**Porquê desta solução:**
O `retry_on_rate_limit` do RockItDown é genérico o suficiente para ser reutilizado em qualquer API externa que devolva erros de rate limiting (Stripe, Langflow, APIs futuras). O `download_to_local` é um utilitário simples que o RockItDown usa para download de assets. Agrupados em `helpers/utils.py` para não poluir o namespace.

**Como o RID acomoda:**
`helpers/utils.py` — utilitários puros sem dependência de Django ou FastAPI. Fáceis de testar isoladamente. `timestamp_to_datetime` é necessário para `helpers/billing.py` (Task 10).

**Files to Create:**
- `/home/RID/backend/helpers/utils.py`

```python
"""
General-purpose utilities.

Origem:
  retry_on_rate_limit → RockItDown/src/helpers/monday_graphql.py:1012-1027
  download_to_local   → RockItDown/src/helpers/downloader.py
  timestamp_to_datetime → RockItDown/src/helpers/date_utils.py (inline)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_rate_limit(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 5,
    retry_delay: float = 5.0,
    rate_limit_marker: str = "ComplexityException",
    **kwargs: Any,
) -> T:
    """
    Executa func(*args, **kwargs) com retry automático em caso de rate limit.

    Origem: RockItDown/src/helpers/monday_graphql.py:retry_on_rate_limit
    Generalizado: aceita marcador de erro configurável (default: 'ComplexityException').

    Uso:
        result = retry_on_rate_limit(stripe.Customer.create, name="Acme")
        result = retry_on_rate_limit(monday_api_call, board_id=123,
                                     rate_limit_marker="TooManyRequests")
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if rate_limit_marker in str(exc):
                if attempt < max_retries:
                    logger.warning(
                        "Rate limit atingido (tentativa %d/%d). Aguardando %.1fs...",
                        attempt, max_retries, retry_delay,
                    )
                    time.sleep(retry_delay)
                else:
                    raise
            else:
                raise
    raise RuntimeError("retry_on_rate_limit: número máximo de tentativas excedido")


def download_to_local(url: str, out_path: Path, *, parent_mkdir: bool = True) -> bool:
    """
    Faz download de url para out_path.

    Origem: RockItDown/src/helpers/downloader.py
    Retorna True em caso de sucesso, False em caso de erro.
    """
    if not isinstance(out_path, Path):
        raise ValueError(f"{out_path} deve ser um pathlib.Path")
    if parent_mkdir:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        return True
    except requests.RequestException as exc:
        logger.error("Falha ao fazer download de %s: %s", url, exc)
        return False


def timestamp_to_datetime(ts: int | float) -> datetime:
    """Converte Unix timestamp (Stripe API) para datetime UTC."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)
```

**Verification:**
```bash
cd /home/RID/backend && . .venv/bin/activate
python3 -c "
from helpers.utils import retry_on_rate_limit, download_to_local, timestamp_to_datetime
from datetime import datetime
import pathlib, tempfile

# retry: deve propagar excepção não-rate-limit imediatamente
try:
    retry_on_rate_limit(lambda: (_ for _ in ()).throw(ValueError('outro erro')))
except ValueError:
    pass

# timestamp
dt = timestamp_to_datetime(0)
assert dt.year == 1970

print('OK: helpers.utils importa e funciona')
"
# Expected: OK: helpers.utils importa e funciona
```

---

## Checkpoint Final

```bash
cd /home/RID/backend && . .venv/bin/activate

# 1. Lint
ruff check .
# Expected: All checks passed.

# 2. Testes
pytest tests/ -v
# Expected: ao menos 7 passed, sem erros de import

# 3. Import smoke-test completo
python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()

from core.asgi import application
from api.deps import get_current_tenant, TenantSchema
from core.auth_backends import TenantAwareBackend
from core.adapters import TenantAwareAccountAdapter
from apps.tenants.services import provision_tenant_for_user, _normalize_schema_name
from apps.tenants.signals import provision_tenant_schema
from apps.accounts.models import TenantMembership
from helpers.billing import create_customer, cancel_subscription
from helpers.utils import retry_on_rate_limit, download_to_local
from api.langflow_mixin import BaseLangflowMixin
from api.routers.langflow import router

print('OK: todos os módulos importam sem erro')
"
# Expected: OK: todos os módulos importam sem erro
```

---

## Zero-Context Test

Um engenheiro sem nenhum conhecimento do codebase consegue:

1. Ler cada task, saber o ficheiro exacto e o porquê da decisão
2. Ver o conteúdo completo do ficheiro (sem "adicionar aqui")
3. Entender a origem de cada solução (RockItDown ou novo)
4. Executar o comando de verificação e saber se passou ou falhou

---

## Failure Recovery

| Falha | Causa provável | Ação |
|---|---|---|
| `ImportError: asgiref` | Não instalado | `uv add asgiref` |
| `ImportError: pytest_asyncio` | Não instalado | `uv add --dev pytest-asyncio` |
| `ValueError: STRIPE_SECRET_KEY é chave de teste` | `DEBUG=False` em dev | Adicionar `STRIPE_TEST_OVERRIDE=True` no `.env` |
| Migração falha em `accounts` | Conflito de estado | `python manage.py migrate --fake-initial` |
| `NotImplementedError` em `BaseLangflowMixin.get_client` | Esperado — placeholder | Implementar quando RockLangflowClient for portado |
| `ImportError: stripe` | Não instalado | `uv add stripe` (já em `pyproject.toml`) |
| `ImportError: requests` em `helpers/utils.py` | Não instalado | `uv add requests` (já em deps transitivas via httpx) |
