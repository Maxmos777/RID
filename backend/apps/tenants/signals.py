"""
Tenant lifecycle signals.

ARQUITECTURA
------------
Este signal é um thin dispatcher — não contém lógica de provisionamento.
A lógica de negócio está em apps.tenants.services.provision_tenant_for_user
(Task 9 deste plano).

Enquanto a task queue (Celery) não está configurada, o provisionamento
corre numa thread de fundo para não bloquear o worker HTTP.

Roadmap:
  Fase 1 (agora): threading.Thread -> desbloqueia worker
  Fase 2 (Task 9): delega a provision_tenant_for_user()
  Fase 3 (futuro): Celery task para retry e observabilidade
"""
from __future__ import annotations

import logging
import threading

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _provision_in_background(schema_name: str, customer_pk) -> None:
    """Corre numa thread de fundo. Erros são logados, não propagados."""
    from apps.tenants.models import Customer

    try:
        instance = Customer.objects.get(pk=customer_pk)
        instance.auto_create_schema = True
        instance.save(update_fields=[])
        instance.auto_create_schema = False
        logger.info("Schema provisionado para tenant: %s", schema_name)
    except Exception:
        logger.exception(
            "Falha ao provisionar schema para tenant %s (pk=%s)",
            schema_name,
            customer_pk,
        )


@receiver(post_save, sender="tenants.Customer")
def provision_tenant_schema(sender, instance, created: bool, **kwargs) -> None:  # type: ignore[no-untyped-def]
    if not created:
        return
    logger.info("Agendando provisão para tenant: %s", instance.schema_name)
    threading.Thread(
        target=_provision_in_background,
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
