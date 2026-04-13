"""TenantAwareBackend — e-mail público não entra no ramo user@tenant."""

from __future__ import annotations

import pytest

from core.auth_backends import TenantAwareBackend


@pytest.mark.django_db
def test_public_email_domain_returns_none() -> None:
    """Login tipo nome@gmail.com deve delegar ao EmailBackend do allauth."""
    backend = TenantAwareBackend()
    assert (
        backend.authenticate(
            None,
            username="alice@gmail.com",
            password="secret",
        )
        is None
    )


@pytest.mark.django_db
def test_rid_domain_without_select_related_full_customer() -> None:
    """Com Domain para hostname RID, autentica sem carregar todas as colunas de Customer."""
    import uuid

    from django.contrib.auth import get_user_model

    from apps.tenants.models import Customer, Domain

    User = get_user_model()
    post_save = __import__("django.db.models.signals", fromlist=["post_save"]).post_save
    from apps.tenants.signals import provision_tenant_schema

    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        schema = f"authbe_{uuid.uuid4().hex[:8]}"
        user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="ok-password-123",
        )
        tenant = Customer.objects.create(schema_name=schema, name="T")
        Domain.objects.create(
            domain=f"{schema}.rid.localhost", tenant=tenant, is_primary=True
        )

        backend = TenantAwareBackend()
        out = backend.authenticate(
            None,
            username=f"bob@{schema}.rid.localhost",
            password="ok-password-123",
        )
        assert out is not None
        assert out.pk == user.pk
    finally:
        post_save.connect(provision_tenant_schema, sender=Customer)
