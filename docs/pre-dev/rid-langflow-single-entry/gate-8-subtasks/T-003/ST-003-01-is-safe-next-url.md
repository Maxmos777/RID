# ST-003-01: Helper is_safe_next_url e URL route /internal/auth-check/

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar o módulo `backend/apps/accounts/auth_gate.py` com a função `is_safe_next_url()`, registar a URL route `GET /internal/auth-check/` em `core/urls.py`, e garantir que o endpoint não requer CSRF.

## Prerequisites

```bash
# T-002 completo — settings de proxy existem
grep -n "SECURE_PROXY_SSL_HEADER" /home/RID/backend/core/settings.py
# Expected output: linha com _proxy_ssl = os.getenv(...)

# urls.py base
cat /home/RID/backend/core/urls.py
# Expected output: urlpatterns com app/, accounts/, admin/

# apps/accounts existe
ls /home/RID/backend/apps/accounts/
# Expected output: __init__.py models.py views.py ...
```

## Files

- **Create:** `backend/apps/accounts/auth_gate.py`
- **Modify:** `backend/core/urls.py`
- **Test:** `backend/tests/test_auth_gate_helpers.py`

## Steps

### Step 1: Escrever o teste (RED)

Criar `/home/RID/backend/tests/test_auth_gate_helpers.py`:

```python
"""Testes unitários para is_safe_next_url (T-003 — rid-langflow-single-entry)."""
from __future__ import annotations

import pytest


class TestIsSafeNextUrl:
    """Tabela de casos válidos e inválidos para is_safe_next_url."""

    def setup_method(self):
        from apps.accounts.auth_gate import is_safe_next_url
        self.fn = is_safe_next_url

    # Casos válidos (deve retornar True)
    @pytest.mark.parametrize("url", [
        "/flows/",
        "/flows/editor?workspace=abc",
        "/app/",
        "/",
        "/internal/auth-check/",
    ])
    def test_valid_internal_paths(self, url: str):
        assert self.fn(url) is True, f"Esperava True para {url!r}"

    # Casos inválidos (deve retornar False)
    @pytest.mark.parametrize("url", [
        "//evil.com",
        "//evil.com/path",
        "https://evil.com",
        "http://evil.com/flows/",
        "javascript:alert(1)",
        "ftp://evil.com",
        "relative/path",
        "",
        "flows/",
        " /flows/",  # espaço antes da barra
    ])
    def test_invalid_urls(self, url: str):
        assert self.fn(url) is False, f"Esperava False para {url!r}"


class TestAuthCheckUrlRegistered:
    """Verifica que /internal/auth-check/ está registado no URLconf."""

    def test_url_resolves(self):
        from django.urls import reverse
        url = reverse("auth-check")
        assert url == "/internal/auth-check/"
```

### Step 2: Correr o teste para confirmar que falha (RED)

```bash
cd /home/RID/backend
python -m pytest tests/test_auth_gate_helpers.py -v 2>&1 | head -20
```

Expected output:
```
ERROR tests/test_auth_gate_helpers.py - ImportError: cannot import name 'is_safe_next_url' from 'apps.accounts.auth_gate'
```

### Step 3: Criar o módulo auth_gate.py

Criar `/home/RID/backend/apps/accounts/auth_gate.py`:

```python
"""Auth Gate helpers — validação de sessão e segurança de URLs (T-003)."""
from __future__ import annotations

import logging
import threading

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def is_safe_next_url(next_url: str) -> bool:
    """
    Valida que next_url é um path interno seguro.

    Aceita apenas paths que comecem com '/' e não sejam protocol-relative
    (iniciados com '//') nem contenham '://' (URLs absolutas).

    Implementação conforme TRD §3.3.
    """
    if not next_url:
        return False
    if not next_url.startswith("/"):
        return False
    if next_url.startswith("//"):
        return False
    if "://" in next_url:
        return False
    return True


def _write_audit_event(
    tenant_schema: str,
    user_id: str,
    user_email: str,
    original_url: str,
) -> None:
    """
    Escreve evento de auditoria de forma assíncrona (fire-and-forget).

    Falha silenciosa — nunca bloqueia a resposta ao cliente.
    """
    try:
        logger.info(
            "langflow_access_granted tenant=%s user_id=%s user_email=%s url=%s",
            tenant_schema,
            user_id,
            user_email,
            original_url,
        )
        # TODO (F-005): substituir por escrita no sistema de auditoria da plataforma
        # quando o modelo AuditEvent estiver disponível.
        # AuditEvent.objects.create(
        #     tenant_schema=tenant_schema,
        #     user_id=user_id,
        #     event_type="langflow_access",
        #     url=original_url,
        # )
    except Exception as exc:  # noqa: BLE001
        # Falha no audit nunca bloqueia o acesso — fire-and-forget
        logger.warning("audit write failed (non-blocking): %s", exc)


@csrf_exempt
@require_GET
def auth_check(request: HttpRequest) -> HttpResponse:
    """
    GET /internal/auth-check/

    Endpoint de validação de sessão e tenant para Traefik forwardAuth.

    Resposta:
      200 — sessão activa + tenant correcto
      401 — sessão ausente ou expirada
      403 — tenant inválido (utilizador não pertence ao tenant do pedido)

    Corpo sempre vazio — Traefik só verifica o status code.
    """
    # 1. Verificar autenticação
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    # 2. Verificar isolamento de tenant
    from django.db import connection
    from django_tenants.utils import get_public_schema_name

    from apps.accounts.models import TenantMembership

    current_schema = getattr(connection, "schema_name", get_public_schema_name())

    # Schema público não é um tenant válido para acesso ao editor
    if current_schema == get_public_schema_name():
        return HttpResponse(status=403)

    # Verificar que o utilizador tem membership no tenant activo
    has_membership = TenantMembership.objects.filter(
        user=request.user,
        tenant_schema=current_schema,
    ).exists()

    if not has_membership:
        return HttpResponse(status=403)

    # 3. Registo de auditoria (fire-and-forget)
    original_url = request.META.get("HTTP_X_FORWARDED_URI", request.path)
    audit_thread = threading.Thread(
        target=_write_audit_event,
        args=(
            current_schema,
            str(request.user.pk),
            str(request.user.email),
            original_url,
        ),
        daemon=True,
    )
    audit_thread.start()

    return HttpResponse(status=200)
```

### Step 4: Registar a URL em core/urls.py

Editar `/home/RID/backend/core/urls.py`:

```python
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.auth_gate import auth_check
from apps.accounts.views import RockItDownSPA

urlpatterns = [
    # /           → /app/
    path("", RedirectView.as_view(url="/app/", permanent=False)),
    # /app/       → RockItDown SPA (LoginRequired)
    path("app/", RockItDownSPA.as_view(), name="rockitdown-spa"),

    # Auth Gate — forwardAuth endpoint para Traefik + heartbeat React
    path("internal/auth-check/", auth_check, name="auth-check"),

    # django-allauth
    path("accounts/", include("allauth.urls")),

    # Django admin
    path("admin/", admin.site.urls),
]
```

### Step 5: Correr os testes (GREEN)

```bash
cd /home/RID/backend
python -m pytest tests/test_auth_gate_helpers.py -v
```

Expected output:
```
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_valid_internal_paths[/flows/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_valid_internal_paths[/flows/editor?workspace=abc] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_valid_internal_paths[/app/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_valid_internal_paths[/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_valid_internal_paths[/internal/auth-check/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[//evil.com] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[//evil.com/path] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[https://evil.com] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[http://evil.com/flows/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[javascript:alert(1)] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[ftp://evil.com] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[relative/path] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[flows/] PASSED
tests/test_auth_gate_helpers.py::TestIsSafeNextUrl::test_invalid_urls[ /flows/] PASSED
tests/test_auth_gate_helpers.py::TestAuthCheckUrlRegistered::test_url_resolves PASSED
16 passed
```

### Step 6: Commit

```bash
cd /home/RID
git add backend/apps/accounts/auth_gate.py backend/core/urls.py backend/tests/test_auth_gate_helpers.py
git commit -m "feat(langflow-gate): add is_safe_next_url helper and auth-check URL route"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
# ou
git checkout -- backend/core/urls.py
rm backend/apps/accounts/auth_gate.py
rm backend/tests/test_auth_gate_helpers.py
```
