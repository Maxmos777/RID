"""
Tenant lifecycle signals.

ARQUITECTURA (ADR-004)
----------------------
Thin dispatcher apenas: threads e chamadas a `apps.tenants.services`.
Toda a lógica de provisionamento vive em services.py.
"""
from __future__ import annotations

import logging
import threading

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.tenants import services as tenant_services

logger = logging.getLogger(__name__)


@receiver(post_save, sender="tenants.Customer")
def provision_tenant_schema(sender, instance, created: bool, **kwargs) -> None:  # type: ignore[no-untyped-def]
    if not created:
        return
    logger.info("Agendando provisão para tenant: %s", instance.schema_name)
    threading.Thread(
        target=tenant_services.run_new_customer_schema_and_langflow_provision,
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
