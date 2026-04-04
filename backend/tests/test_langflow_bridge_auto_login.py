"""Testes ASGI do endpoint GET /api/v1/langflow/auth/auto-login (bridge Opção C)."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.db.models.signals import post_save
from starlette.testclient import TestClient

from apps.accounts.models import TenantMembership, TenantUser
from apps.tenants.models import Customer, Domain
from apps.tenants.signals import provision_tenant_schema
from core.asgi import application


@pytest.fixture
def sync_api_client():
    with TestClient(application) as c:
        yield c


@pytest.fixture
def rid_user_and_tenant(db):
    """Um utilizador, um tenant com domínio, membership e workspace Langflow."""
    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"u-{uuid.uuid4().hex[:8]}",
            email=f"u-{uuid.uuid4().hex[:8]}@example.com",
            password="pw",
        )
        schema = f"t_{uuid.uuid4().hex[:8]}"
        tenant = Customer.objects.create(
            schema_name=schema,
            name="T",
            langflow_workspace_id=uuid.uuid4(),
        )
        host = f"{schema}.rid.localhost"
        Domain.objects.create(domain=host, tenant=tenant, is_primary=True)
        TenantMembership.objects.create(
            user=user,
            tenant_schema=schema,
            role="member",
        )
        store = SessionStore()
        store["_auth_user_id"] = str(user.pk)
        store.create()
        yield user, tenant, host, store.session_key
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)


@pytest.mark.django_db(transaction=True)
def test_auto_login_200_returns_workspace(
    sync_api_client,
    rid_user_and_tenant,
    settings,
) -> None:
    settings.LANGFLOW_BASE_URL = "http://langflow.test"
    _user, tenant, host, session_key = rid_user_and_tenant

    mock_creds = AsyncMock(
        return_value=(
            {"access_token": "jwt", "api_key": "sk", "user_id": ""},
            None,
        ),
    )
    with patch(
        "api.routers.langflow_auth.get_tenant_service_credentials",
        mock_creds,
    ):
        r = sync_api_client.get(
            "/api/v1/langflow/auth/auto-login",
            cookies={"sessionid": session_key},
            headers={"Host": host},
        )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] == "jwt"
    assert data["api_key"] == "sk"
    assert data["workspace_id"] == str(tenant.langflow_workspace_id)
    assert data["langflow_user_id"] is None
    mock_creds.assert_awaited_once()


@pytest.mark.django_db(transaction=True)
def test_auto_login_409_without_workspace(
    sync_api_client,
    rid_user_and_tenant,
    settings,
) -> None:
    settings.LANGFLOW_BASE_URL = "http://langflow.test"
    _user, tenant, host, session_key = rid_user_and_tenant
    Customer.objects.filter(pk=tenant.pk).update(langflow_workspace_id=None)

    r = sync_api_client.get(
        "/api/v1/langflow/auth/auto-login",
        cookies={"sessionid": session_key},
        headers={"Host": host},
    )
    assert r.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_auto_login_403_not_member(
    sync_api_client,
    rid_user_and_tenant,
    settings,
) -> None:
    settings.LANGFLOW_BASE_URL = "http://langflow.test"
    _user, tenant, host, session_key = rid_user_and_tenant
    TenantMembership.objects.filter(tenant_schema=tenant.schema_name).delete()

    r = sync_api_client.get(
        "/api/v1/langflow/auth/auto-login",
        cookies={"sessionid": session_key},
        headers={"Host": host},
    )
    assert r.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_auto_login_400_multi_tenant_without_query(sync_api_client, settings) -> None:
    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"m-{uuid.uuid4().hex[:8]}",
            email=f"m-{uuid.uuid4().hex[:8]}@example.com",
            password="pw",
        )
        s1 = f"a_{uuid.uuid4().hex[:6]}"
        s2 = f"b_{uuid.uuid4().hex[:6]}"
        t1 = Customer.objects.create(schema_name=s1, name="A", langflow_workspace_id=uuid.uuid4())
        Customer.objects.create(schema_name=s2, name="B", langflow_workspace_id=uuid.uuid4())
        Domain.objects.create(domain=f"{s1}.rid.localhost", tenant=t1, is_primary=True)
        TenantMembership.objects.create(user=user, tenant_schema=s1, role="member")
        TenantMembership.objects.create(user=user, tenant_schema=s2, role="member")
        store = SessionStore()
        store["_auth_user_id"] = str(user.pk)
        store.create()

        r = sync_api_client.get(
            "/api/v1/langflow/auth/auto-login",
            cookies={"sessionid": store.session_key},
            headers={"Host": f"{s1}.rid.localhost"},
        )
        assert r.status_code == 400
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)


@pytest.mark.django_db(transaction=True)
def test_auto_login_200_with_tenant_schema_query(sync_api_client, settings) -> None:
    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"m2-{uuid.uuid4().hex[:8]}",
            email=f"m2-{uuid.uuid4().hex[:8]}@example.com",
            password="pw",
        )
        s1 = f"c_{uuid.uuid4().hex[:6]}"
        s2 = f"d_{uuid.uuid4().hex[:6]}"
        w1 = uuid.uuid4()
        tenant_c = Customer.objects.create(
            schema_name=s1,
            name="C",
            langflow_workspace_id=w1,
        )
        Customer.objects.create(
            schema_name=s2,
            name="D",
            langflow_workspace_id=uuid.uuid4(),
        )
        Domain.objects.create(
            domain=f"{s1}.rid.localhost",
            tenant=tenant_c,
            is_primary=True,
        )
        TenantMembership.objects.create(user=user, tenant_schema=s1, role="member")
        TenantMembership.objects.create(user=user, tenant_schema=s2, role="member")
        store = SessionStore()
        store["_auth_user_id"] = str(user.pk)
        store.create()

        mock_creds = AsyncMock(
            return_value=(
                {"access_token": "j2", "api_key": "k2", "user_id": ""},
                None,
            ),
        )
        with patch(
            "api.routers.langflow_auth.get_tenant_service_credentials",
            mock_creds,
        ):
            r = sync_api_client.get(
                "/api/v1/langflow/auth/auto-login",
                params={"tenant_schema": s1},
                cookies={"sessionid": store.session_key},
                headers={"Host": "localhost"},
            )
        assert r.status_code == 200, r.text
        assert r.json()["workspace_id"] == str(w1)
        mock_creds.assert_awaited_once_with(s1, None)
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)
