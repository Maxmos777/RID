"""Integration tests for auth_gate — covers end-to-end auth-check scenarios."""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models.signals import post_save
from django.test import RequestFactory

from apps.accounts.auth_gate import auth_check, is_safe_next_url
from apps.accounts.models import TenantMembership
from apps.tenants.models import Customer
from apps.tenants.signals import provision_tenant_schema

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _disconnect_provision_signal():
    """Prevent tenant schema provisioning during tests."""
    post_save.disconnect(provision_tenant_schema, sender=Customer)
    yield
    post_save.connect(provision_tenant_schema, sender=Customer)


@pytest.fixture
def factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def tenant_schema() -> str:
    return f"tenant_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def other_tenant_schema() -> str:
    return f"other_{uuid.uuid4().hex[:8]}"


def _build_get(factory: RequestFactory, user=None, **meta):
    """Build a GET request with an attached user."""
    request = factory.get("/internal/auth-check/", **meta)
    request.user = user if user is not None else AnonymousUser()
    return request


# ---------------------------------------------------------------------------
# Scenario 1: Unauthenticated access
# ---------------------------------------------------------------------------


class TestScenario1UnauthenticatedAccess:
    """Anonymous requests must receive 401 with empty body."""

    def test_anonymous_returns_401(self, factory: RequestFactory) -> None:
        request = _build_get(factory)
        response = auth_check(request)
        assert response.status_code == 401

    def test_anonymous_body_is_empty(self, factory: RequestFactory) -> None:
        request = _build_get(factory)
        response = auth_check(request)
        assert response.content == b""


# ---------------------------------------------------------------------------
# Scenario 2: Authenticated user on correct tenant
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScenario2AuthenticatedCorrectTenant:
    """Authenticated user with active membership on current tenant -> 200."""

    @pytest.fixture
    def member_user(self, tenant_schema: str):
        user = User.objects.create_user(
            username=f"member_{uuid.uuid4().hex[:6]}",
            email="member@example.com",
            password="testpass123",
        )
        TenantMembership.objects.create(
            user=user,
            tenant_schema=tenant_schema,
            role="member",
            is_active=True,
        )
        return user

    def test_returns_200(
        self,
        factory: RequestFactory,
        member_user,
        tenant_schema: str,
    ) -> None:
        request = _build_get(factory, user=member_user)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            response = auth_check(request)
        assert response.status_code == 200

    def test_body_is_empty(
        self,
        factory: RequestFactory,
        member_user,
        tenant_schema: str,
    ) -> None:
        request = _build_get(factory, user=member_user)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            response = auth_check(request)
        assert response.content == b""


# ---------------------------------------------------------------------------
# Scenario 3 & 5: Tenant isolation — wrong tenant, no membership, inactive
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScenario3And5TenantIsolation:
    """Users without valid active membership on current tenant -> 403."""

    @pytest.fixture
    def user_with_membership(self, tenant_schema: str):
        """User with active membership on tenant_schema."""
        user = User.objects.create_user(
            username=f"iso_{uuid.uuid4().hex[:6]}",
            email="iso@example.com",
            password="testpass123",
        )
        TenantMembership.objects.create(
            user=user,
            tenant_schema=tenant_schema,
            role="member",
            is_active=True,
        )
        return user

    @pytest.fixture
    def user_no_membership(self):
        return User.objects.create_user(
            username=f"nomb_{uuid.uuid4().hex[:6]}",
            email="nomb@example.com",
            password="testpass123",
        )

    def test_wrong_tenant_returns_403(
        self,
        factory: RequestFactory,
        user_with_membership,
        other_tenant_schema: str,
    ) -> None:
        """User has membership on tenant_schema but request hits other_tenant."""
        request = _build_get(factory, user=user_with_membership)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = other_tenant_schema
            response = auth_check(request)
        assert response.status_code == 403

    def test_no_membership_returns_403(
        self,
        factory: RequestFactory,
        user_no_membership,
        tenant_schema: str,
    ) -> None:
        request = _build_get(factory, user=user_no_membership)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            response = auth_check(request)
        assert response.status_code == 403

    def test_inactive_membership_returns_403(
        self,
        factory: RequestFactory,
        tenant_schema: str,
    ) -> None:
        user = User.objects.create_user(
            username=f"inact_{uuid.uuid4().hex[:6]}",
            email="inactive@example.com",
            password="testpass123",
        )
        TenantMembership.objects.create(
            user=user,
            tenant_schema=tenant_schema,
            role="member",
            is_active=False,
        )
        request = _build_get(factory, user=user)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            response = auth_check(request)
        assert response.status_code == 403

    def test_public_schema_returns_403(
        self,
        factory: RequestFactory,
        user_with_membership,
    ) -> None:
        """Even with membership, public schema has no match -> 403."""
        request = _build_get(factory, user=user_with_membership)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = "public"
            response = auth_check(request)
        assert response.status_code == 403

    def test_403_body_is_empty(
        self,
        factory: RequestFactory,
        user_no_membership,
        tenant_schema: str,
    ) -> None:
        request = _build_get(factory, user=user_no_membership)
        with patch("apps.accounts.auth_gate.connection") as mock_conn:
            mock_conn.schema_name = tenant_schema
            response = auth_check(request)
        assert response.content == b""


# ---------------------------------------------------------------------------
# Scenario 7: is_safe_next_url — open-redirect prevention
# ---------------------------------------------------------------------------


SAFE_URLS = [
    pytest.param("/", id="root"),
    pytest.param("/flows/", id="flows"),
    pytest.param("/flows/editor?workspace=abc", id="with-query"),
    pytest.param("/app/dashboard", id="nested-path"),
    pytest.param("/internal/auth-check/", id="internal"),
]

UNSAFE_URLS = [
    pytest.param("//evil.com", id="protocol-relative"),
    pytest.param("https://evil.com", id="absolute-https"),
    pytest.param("http://evil.com", id="absolute-http"),
    pytest.param("javascript:alert(1)", id="javascript-scheme"),
    pytest.param("ftp://evil.com/file", id="ftp-scheme"),
    pytest.param("", id="empty-string"),
    pytest.param("relative/path", id="relative-no-slash"),
    pytest.param(" /flows/", id="leading-space"),
    pytest.param(None, id="none-value"),
    pytest.param(42, id="non-string"),
]


class TestScenario7IsSafeNextUrl:
    """Parametrized tests for open-redirect prevention."""

    @pytest.mark.parametrize("url", SAFE_URLS)
    def test_safe_urls_accepted(self, url: str) -> None:
        assert is_safe_next_url(url) is True

    @pytest.mark.parametrize("url", UNSAFE_URLS)
    def test_unsafe_urls_rejected(self, url) -> None:
        assert is_safe_next_url(url) is False
