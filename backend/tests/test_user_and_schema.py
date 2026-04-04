from __future__ import annotations

import uuid

import pytest
from django.db import connection
from django.db.models.signals import post_save

from api.deps import _resolve_tenant
from apps.accounts.models import TenantMembership, TenantUser
from apps.tenants.models import Customer, Domain
from apps.tenants.signals import provision_tenant_schema


@pytest.mark.django_db(transaction=True)
def test_create_user_and_verify_schema_resolution_sets_search_path():
    """
    Cria TenantUser (schema público) + Customer/Domain (tenant),
    e valida que a resolução do TenantSchema ajusta o schema ativo
    no PostgreSQL connection via search_path.
    """

    # Evita a thread em background do signal de provisioning de schema.
    # Para este teste, basta validar que connection.set_tenant ajusta o
    # contexto do schema (search_path), não que o schema já tenha tabelas.
    post_save.disconnect(provision_tenant_schema, sender=Customer)
    try:
        user = TenantUser.objects.create_user(
            username=f"user-{uuid.uuid4().hex[:8]}",
            email=f"user-{uuid.uuid4().hex[:8]}@example.com",
            password="test-password-123",
        )

        schema_name = f"tenant_test_{uuid.uuid4().hex[:8]}"
        tenant = Customer.objects.create(schema_name=schema_name, name="Test Tenant")
        hostname = f"{schema_name}.rid.localhost"
        Domain.objects.create(domain=hostname, tenant=tenant, is_primary=True)

        TenantMembership.objects.create(
            user=user,
            tenant_schema=tenant.schema_name,
            role="member",
        )

        resolved_schema = _resolve_tenant(hostname)
        assert resolved_schema == tenant.schema_name

        # Validação do estado interno da conexão (django-tenants).
        assert getattr(connection, "schema_name", None) == tenant.schema_name

        # Validação explícita via search_path do PostgreSQL.
        with connection.cursor() as cursor:
            cursor.execute("SHOW search_path")
            search_path = cursor.fetchone()[0]

        parts = [p.strip().strip('"') for p in search_path.split(",") if p.strip()]
        assert parts[0] == tenant.schema_name
        assert "public" in parts

        # E confirma que queries dos apps em public continuam resolvíveis.
        assert TenantUser.objects.filter(pk=user.pk).exists()
    finally:
        connection.set_schema_to_public()
        post_save.connect(provision_tenant_schema, sender=Customer)

