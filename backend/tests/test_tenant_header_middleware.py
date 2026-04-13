"""Resolução de tenant por cabeçalho X-Tenant-Id (HeaderFirstTenantMiddleware)."""

from __future__ import annotations

import uuid

import pytest
from django.db import connection
from django.db.models.signals import post_save
from django.test import RequestFactory, override_settings

from apps.tenants.models import Customer, Domain
from apps.tenants.signals import provision_tenant_schema


@pytest.mark.django_db(transaction=True)
def test_middleware_sets_tenant_from_x_tenant_id_header() -> None:
    from core.tenant_middleware import HeaderFirstTenantMiddleware

    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        schema_name = f"hdr_{uuid.uuid4().hex[:8]}"
        tenant = Customer.objects.create(schema_name=schema_name, name="Header test")
        Domain.objects.create(
            domain=f"{schema_name}.rid.localhost",
            tenant=tenant,
            is_primary=True,
        )

        request = RequestFactory().get(
            "/",
            HTTP_HOST="localhost",
            HTTP_X_TENANT_ID=str(tenant.public_tenant_id),
        )
        with override_settings(TENANT_RESOLUTION_HEADER="HTTP_X_TENANT_ID"):
            mw = HeaderFirstTenantMiddleware(get_response=lambda r: None)
            assert mw.process_request(request) is None

        assert request.tenant == tenant
        assert connection.schema_name == tenant.schema_name
    finally:
        connection.set_schema_to_public()
        post_save.connect(provision_tenant_schema, sender=Customer)
