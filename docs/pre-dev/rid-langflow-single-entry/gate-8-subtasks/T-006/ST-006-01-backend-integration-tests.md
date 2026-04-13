# ST-006-01: Testes de integração backend (cenários 1, 2, 3, 5, 7)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar a suite de testes de integração em `backend/tests/test_auth_gate_integration.py` cobrindo: acesso não autenticado → 401 (Cenário 1), acesso autenticado com tenant correcto → 200 (Cenário 2), mismatch de tenant → 403 (Cenário 3/5), e `is_safe_next_url` edge cases (Cenário 7 parcial).

## Prerequisites

```bash
# T-003 completo — auth_check view e auth_gate.py existem
python -c "from apps.accounts.auth_gate import auth_check, is_safe_next_url; print('OK')" 2>/dev/null \
  || cd /home/RID/backend && python -c "from apps.accounts.auth_gate import auth_check, is_safe_next_url; print('OK')"

# T-002 completo — settings de proxy existem
grep -n "SESSION_COOKIE_SAMESITE" /home/RID/backend/core/settings.py
# Expected output: SESSION_COOKIE_SAMESITE = "Lax"

# conftest.py existente para verificar padrões de fixtures
cat /home/RID/backend/tests/conftest.py
# Expected output: fixtures asgi_app e client
```

## Files

- **Test:** `backend/tests/test_auth_gate_integration.py`

## Steps

### Step 1: Escrever os testes de integração (RED)

Criar `/home/RID/backend/tests/test_auth_gate_integration.py`:

```python
"""
Testes de integração para o Auth Gate endpoint (T-006 — rid-langflow-single-entry).

Cenários cobertos:
  - Cenário 1: acesso não autenticado → 401
  - Cenário 2: acesso autenticado + tenant correcto → 200
  - Cenário 3: acesso autenticado + tenant errado → 403
  - Cenário 5: isolamento de tenant (utilizador de outro tenant) → 403
  - is_safe_next_url: edge cases de open redirect

Nota: Cenário 4 (Langflow indisponível → error page) e Cenário 6 (WebSocket)
cobertos em ST-006-02 (requerem stack completo com Traefik + Docker Compose).
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.test import Client, RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser
from django.db.models.signals import post_save

from apps.accounts.auth_gate import auth_check, is_safe_next_url


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def schema_a():
    return f"t_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def schema_b():
    return f"t_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def user_in_tenant_a(db, schema_a):
    """Utilizador com membership no tenant A."""
    from apps.accounts.models import TenantMembership, TenantUser
    from apps.tenants.signals import provision_tenant_schema
    from apps.tenants.models import Customer

    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"u-{uuid.uuid4().hex[:8]}",
            email=f"u-{uuid.uuid4().hex[:8]}@example.com",
            password="pw-secure-123",
        )
        TenantMembership.objects.create(
            user=user,
            tenant_schema=schema_a,
            role="member",
        )
        return user
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)


@pytest.fixture
def user_in_tenant_b(db, schema_b):
    """Utilizador com membership apenas no tenant B."""
    from apps.accounts.models import TenantMembership, TenantUser
    from apps.tenants.signals import provision_tenant_schema
    from apps.tenants.models import Customer

    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"u-{uuid.uuid4().hex[:8]}",
            email=f"u-{uuid.uuid4().hex[:8]}@example.com",
            password="pw-secure-123",
        )
        TenantMembership.objects.create(
            user=user,
            tenant_schema=schema_b,
            role="member",
        )
        return user
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)


# ---------------------------------------------------------------------------
# Cenário 1: acesso não autenticado
# ---------------------------------------------------------------------------

class TestScenario1UnauthenticatedAccess:
    """Cenário 1: GET /internal/auth-check/ sem sessão → 401."""

    def test_anonymous_returns_401(self, rf):
        request = rf.get("/internal/auth-check/")
        request.user = AnonymousUser()
        response = auth_check(request)
        assert response.status_code == 401

    def test_401_body_is_empty(self, rf):
        request = rf.get("/internal/auth-check/")
        request.user = AnonymousUser()
        response = auth_check(request)
        assert response.content == b""

    @pytest.mark.django_db
    def test_django_test_client_no_session_returns_401(self):
        client = Client()
        response = client.get("/internal/auth-check/")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Cenário 2: acesso autenticado com tenant correcto
# ---------------------------------------------------------------------------

class TestScenario2AuthenticatedCorrectTenant:
    """Cenário 2: sessão válida + tenant correcto → 200."""

    @pytest.mark.django_db
    def test_authenticated_user_correct_tenant_returns_200(
        self, rf, user_in_tenant_a, schema_a
    ):
        request = rf.get("/internal/auth-check/")
        request.user = user_in_tenant_a

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = schema_a
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_200_body_is_empty(self, rf, user_in_tenant_a, schema_a):
        request = rf.get("/internal/auth-check/")
        request.user = user_in_tenant_a

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = schema_a
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.content == b""


# ---------------------------------------------------------------------------
# Cenário 3 + 5: isolamento de tenant
# ---------------------------------------------------------------------------

class TestScenario3And5TenantIsolation:
    """Cenários 3 e 5: utilizador de tenant errado → 403."""

    @pytest.mark.django_db
    def test_user_tenant_b_accessing_tenant_a_returns_403(
        self, rf, user_in_tenant_b, schema_a
    ):
        """Utilizador do tenant B tenta aceder ao editor do tenant A → 403."""
        request = rf.get("/internal/auth-check/")
        request.user = user_in_tenant_b

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = schema_a
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_403_body_is_empty(self, rf, user_in_tenant_b, schema_a):
        request = rf.get("/internal/auth-check/")
        request.user = user_in_tenant_b

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = schema_a
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.content == b""

    @pytest.mark.django_db
    def test_user_without_any_membership_returns_403(self, rf, schema_a):
        """Utilizador sem nenhuma membership → 403."""
        from apps.accounts.models import TenantUser

        user = TenantUser.objects.create_user(
            username=f"u-{uuid.uuid4().hex[:8]}",
            email=f"u-{uuid.uuid4().hex[:8]}@example.com",
            password="pw-secure-123",
        )
        request = rf.get("/internal/auth-check/")
        request.user = user

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = schema_a
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Cenário 7 parcial: is_safe_next_url edge cases (open redirect prevention)
# ---------------------------------------------------------------------------

class TestScenario7IsSafeNextUrl:
    """Validação de open redirect no parâmetro next (TRD §3.3)."""

    @pytest.mark.parametrize("safe_url", [
        "/flows/",
        "/app/",
        "/",
        "/flows/editor?workspace=abc123",
        "/internal/auth-check/",
    ])
    def test_safe_internal_paths(self, safe_url: str):
        assert is_safe_next_url(safe_url) is True

    @pytest.mark.parametrize("unsafe_url", [
        "//evil.com",
        "//evil.com/path",
        "https://evil.com",
        "http://evil.com/flows/",
        "javascript:alert(document.cookie)",
        "ftp://files.evil.com",
        "relative/without/leading/slash",
        "",
        "flows/",
    ])
    def test_unsafe_open_redirect_urls(self, unsafe_url: str):
        assert is_safe_next_url(unsafe_url) is False
```

### Step 2: Correr para verificar que passam (todos os testes dependem de T-003 estar completo)

```bash
cd /home/RID/backend
python -m pytest tests/test_auth_gate_integration.py -v
```

Expected output:
```
tests/test_auth_gate_integration.py::TestScenario1UnauthenticatedAccess::test_anonymous_returns_401 PASSED
tests/test_auth_gate_integration.py::TestScenario1UnauthenticatedAccess::test_401_body_is_empty PASSED
tests/test_auth_gate_integration.py::TestScenario1UnauthenticatedAccess::test_django_test_client_no_session_returns_401 PASSED
tests/test_auth_gate_integration.py::TestScenario2AuthenticatedCorrectTenant::test_authenticated_user_correct_tenant_returns_200 PASSED
tests/test_auth_gate_integration.py::TestScenario2AuthenticatedCorrectTenant::test_200_body_is_empty PASSED
tests/test_auth_gate_integration.py::TestScenario3And5TenantIsolation::test_user_tenant_b_accessing_tenant_a_returns_403 PASSED
tests/test_auth_gate_integration.py::TestScenario3And5TenantIsolation::test_403_body_is_empty PASSED
tests/test_auth_gate_integration.py::TestScenario3And5TenantIsolation::test_user_without_any_membership_returns_403 PASSED
tests/test_auth_gate_integration.py::TestScenario7IsSafeNextUrl::test_safe_internal_paths[/flows/] PASSED
...
16 passed
```

### Step 3: Correr a suite completa de testes backend para verificar que não houve regressões

```bash
cd /home/RID/backend
python -m pytest tests/ -v 2>&1 | tail -15
```

Expected output:
```
... passed, 0 failed
```

### Step 4: Commit

```bash
cd /home/RID
git add backend/tests/test_auth_gate_integration.py
git commit -m "test(langflow-gate): add backend integration tests for auth gate (scenarios 1, 2, 3, 5, 7)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
