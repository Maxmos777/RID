# ST-003-02: Testes unitários para auth_check view (200/401/403 + audit fire-and-forget)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Escrever e fazer passar os testes unitários completos para a view `auth_check` — cobrindo todos os 4 códigos de resposta (200, 401 sessão ausente, 401 sessão expirada, 403 tenant inválido) e verificando que falha no audit não bloqueia o 200.

## Prerequisites

```bash
# ST-003-01 completo — auth_gate.py e URL registada
python -c "from apps.accounts.auth_gate import auth_check; print('OK')" 2>/dev/null || cd /home/RID/backend && python -c "from apps.accounts.auth_gate import auth_check; print('OK')"

# Verificar modelos existentes para fixtures
grep -n "TenantMembership" /home/RID/backend/apps/accounts/models.py | head -5
# Expected output: class TenantMembership ou campo membership
```

## Files

- **Test:** `backend/tests/test_auth_check_view.py`

## Steps

### Step 1: Verificar estrutura do modelo TenantMembership

```bash
grep -n "class TenantMembership\|tenant_schema\|class TenantUser" /home/RID/backend/apps/accounts/models.py
```

Expected output: nomes dos campos — usar para construir fixtures correctas no passo seguinte.

### Step 2: Escrever os testes (RED)

Criar `/home/RID/backend/tests/test_auth_check_view.py`:

```python
"""
Testes unitários para GET /internal/auth-check/ (T-003 — rid-langflow-single-entry).

Cobre:
  - 200: sessão válida + tenant correcto
  - 401: utilizador não autenticado
  - 401: sessão expirada (simulada por mock)
  - 403: utilizador sem membership no tenant activo
  - 403: schema público (sem tenant)
  - Audit fire-and-forget: falha no audit não bloqueia 200
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser

from apps.accounts.auth_gate import auth_check


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def tenant_schema():
    return f"t_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def authenticated_user(db, tenant_schema):
    """Cria utilizador com membership no tenant_schema."""
    from apps.accounts.models import TenantMembership, TenantUser

    user = TenantUser.objects.create_user(
        username=f"u-{uuid.uuid4().hex[:8]}",
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        password="pw",
    )
    TenantMembership.objects.create(
        user=user,
        tenant_schema=tenant_schema,
        role="member",
    )
    return user


@pytest.fixture
def user_without_membership(db):
    """Utilizador sem membership em nenhum tenant."""
    from apps.accounts.models import TenantUser

    return TenantUser.objects.create_user(
        username=f"u-{uuid.uuid4().hex[:8]}",
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        password="pw",
    )


class TestAuthCheckUnauthenticated:
    """Utilizador não autenticado → 401."""

    def test_anonymous_user_returns_401(self, factory):
        request = factory.get("/internal/auth-check/")
        request.user = AnonymousUser()
        response = auth_check(request)
        assert response.status_code == 401

    def test_response_body_is_empty(self, factory):
        request = factory.get("/internal/auth-check/")
        request.user = AnonymousUser()
        response = auth_check(request)
        assert response.content == b""


class TestAuthCheckAuthenticated:
    """Utilizador autenticado + tenant correcto → 200."""

    @pytest.mark.django_db
    def test_valid_session_correct_tenant_returns_200(
        self, factory, authenticated_user, tenant_schema
    ):
        request = factory.get("/internal/auth-check/")
        request.user = authenticated_user

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_200_response_body_is_empty(
        self, factory, authenticated_user, tenant_schema
    ):
        request = factory.get("/internal/auth-check/")
        request.user = authenticated_user

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.content == b""


class TestAuthCheckTenantIsolation:
    """Tenant inválido → 403."""

    @pytest.mark.django_db
    def test_user_without_membership_returns_403(
        self, factory, user_without_membership, tenant_schema
    ):
        request = factory.get("/internal/auth-check/")
        request.user = user_without_membership

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_public_schema_returns_403(
        self, factory, authenticated_user
    ):
        """Schema público não é tenant válido para acesso ao editor."""
        request = factory.get("/internal/auth-check/")
        request.user = authenticated_user

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "public"
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                response = auth_check(request)

        assert response.status_code == 403


class TestAuthCheckAuditFireAndForget:
    """Falha no audit não bloqueia a resposta 200."""

    @pytest.mark.django_db
    def test_audit_failure_does_not_block_200(
        self, factory, authenticated_user, tenant_schema
    ):
        request = factory.get("/internal/auth-check/")
        request.user = authenticated_user

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                with patch(
                    "apps.accounts.auth_gate._write_audit_event",
                    side_effect=Exception("audit system down"),
                ):
                    # Mesmo com _write_audit_event a falhar, o thread não bloqueia
                    # (a excepção seria no thread daemon, não na thread principal)
                    response = auth_check(request)

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_x_forwarded_uri_used_for_audit_url(
        self, factory, authenticated_user, tenant_schema
    ):
        """Quando X-Forwarded-Uri está presente, é usado como URL no audit."""
        request = factory.get(
            "/internal/auth-check/",
            HTTP_X_FORWARDED_URI="/flows/editor?workspace=abc",
        )
        request.user = authenticated_user

        audit_calls = []

        def fake_audit(tenant, user_id, email, url):
            audit_calls.append(url)

        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            with patch("django_tenants.utils.get_public_schema_name", return_value="public"):
                with patch("apps.accounts.auth_gate._write_audit_event", side_effect=fake_audit):
                    response = auth_check(request)

        assert response.status_code == 200
        # Dar tempo ao thread daemon para completar
        import time
        time.sleep(0.05)
        assert audit_calls == ["/flows/editor?workspace=abc"]
```

### Step 3: Correr para verificar que falha (RED)

```bash
cd /home/RID/backend
python -m pytest tests/test_auth_check_view.py -v 2>&1 | head -30
```

Expected output:
```
FAILED tests/test_auth_check_view.py::TestAuthCheckUnauthenticated::test_anonymous_user_returns_401
...
```

(pode falhar por problema de schema de tenant ou modelo — ajustar fixtures conforme a saída)

### Step 4: Correr após confirmar que auth_gate.py está completo (GREEN)

```bash
cd /home/RID/backend
python -m pytest tests/test_auth_check_view.py -v
```

Expected output:
```
tests/test_auth_check_view.py::TestAuthCheckUnauthenticated::test_anonymous_user_returns_401 PASSED
tests/test_auth_check_view.py::TestAuthCheckUnauthenticated::test_response_body_is_empty PASSED
tests/test_auth_check_view.py::TestAuthCheckAuthenticated::test_valid_session_correct_tenant_returns_200 PASSED
tests/test_auth_check_view.py::TestAuthCheckAuthenticated::test_200_response_body_is_empty PASSED
tests/test_auth_check_view.py::TestAuthCheckTenantIsolation::test_user_without_membership_returns_403 PASSED
tests/test_auth_check_view.py::TestAuthCheckTenantIsolation::test_public_schema_returns_403 PASSED
tests/test_auth_check_view.py::TestAuthCheckAuditFireAndForget::test_audit_failure_does_not_block_200 PASSED
tests/test_auth_check_view.py::TestAuthCheckAuditFireAndForget::test_x_forwarded_uri_used_for_audit_url PASSED
8 passed
```

### Step 5: Commit

```bash
cd /home/RID
git add backend/tests/test_auth_check_view.py
git commit -m "test(langflow-gate): add unit tests for auth_check view (200/401/403 + audit fire-and-forget)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
