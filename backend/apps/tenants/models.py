"""
Multi-tenancy models.

Customer  — the tenant (one PostgreSQL schema per customer)
Domain    — maps hostnames to tenants
"""
from __future__ import annotations

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

__all__ = ["Customer", "Domain"]


class Customer(TenantMixin):
    """
    One row per tenant. django-tenants creates/drops the PostgreSQL schema
    automatically when this model is saved/deleted.

    auto_create_schema = False — schemas are created explicitly via a
    post-save signal to avoid blocking HTTP requests during signup.
    """

    auto_create_schema = False  # Schema created asynchronously — see apps/tenants/signals.py

    # Business fields
    name = models.CharField(max_length=255, default="")
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    plan = models.CharField(
        max_length=50,
        choices=[
            ("free", "Free"),
            ("basic", "Basic"),
            ("pro", "Pro"),
            ("enterprise", "Enterprise"),
        ],
        default="free",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Langflow 1.8.x: "workspace" do plano arquitectural = project (Folder) na API.
    # Provisionado via utilizador de serviço por tenant (api/services/langflow_workspace.py).
    langflow_workspace_id = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        help_text="UUID do project Langflow (Folder) dedicado ao tenant.",
    )
    langflow_service_api_key = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="API key em cache do utilizador de serviço Langflow (rid.svc.<schema>).",
    )

    class Meta:
        app_label = "tenants"

    def __str__(self) -> str:
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """
    Maps a hostname (e.g. acme.rockitdown.com) to a Customer schema.
    is_primary=True marks the canonical domain used for redirects.
    """

    class Meta:
        app_label = "tenants"

    def __str__(self) -> str:
        return self.domain
