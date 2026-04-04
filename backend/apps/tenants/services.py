"""
Tenant provisioning service layer.

Origem: RockItDown/src/customers/services.py (adaptado).
Diferenças:
  - Usa campo `name` em vez de `tenant_name`/`username` (modelo RID)
  - Usa `migrate_schemas` management command via tenant_context
  - Não guarda utilizador no schema do tenant (utilizadores no schema público no RID)

Idempotência: safe to call multiple times — verifica existência antes de criar.
"""
from __future__ import annotations

import logging
import re
from typing import Tuple

from asgiref.sync import async_to_sync
from django.core.management import call_command
from django.utils.text import slugify
from django_tenants.utils import tenant_context

from apps.tenants.models import Customer, Domain

logger = logging.getLogger(__name__)

# Inclui nomes que colidem com schemas de plataforma (Langflow em ADR-009).
RESERVED_SCHEMAS = frozenset(
    {"public", "information_schema", "pg_catalog", "langflow"},
)


def _normalize_schema_name(raw: str) -> str:
    """Converte nome arbitrário em schema_name válido para PostgreSQL."""
    base = slugify(raw or "").replace("-", "_")
    base = re.sub(r"[^a-z0-9_]+", "", base)
    return base[:48]  # PostgreSQL max identifier length é 63; 48 dá margem


def _ensure_unique_domain(base_domain: str) -> str:
    """Garante que o domínio não está em uso, adicionando sufixo numérico se necessário."""
    candidate = base_domain
    suffix = 1
    while Domain.objects.filter(domain__iexact=candidate).exists():
        suffix += 1
        candidate = f"{base_domain}{suffix}"
    return candidate


def provision_tenant_for_user(
    *,
    user,
    tenant_name: str,
    primary_domain_suffix: str = "rid.localhost",
) -> Tuple["Customer", "Domain"]:
    """
    Cria Customer + Domain, migra schema e retorna (tenant, domain).

    Idempotente: se o tenant já existir com o mesmo schema_name, retorna-o.
    O utilizador não é movido para o schema do tenant — no RID os utilizadores
    ficam no schema público (SHARED_APPS).

    Args:
        user: instância de TenantUser (já guardada no schema público)
        tenant_name: nome legível do tenant (e.g. "Acme Corp")
        primary_domain_suffix: sufixo de domínio (default: rid.localhost para dev)

    Returns:
        (Customer, Domain) — o tenant e o domínio primário

    Raises:
        ValueError: se tenant_name resultar num schema_name inválido ou reservado
    """
    schema_name = _normalize_schema_name(tenant_name)
    if not schema_name or schema_name in RESERVED_SCHEMAS:
        raise ValueError(f"Nome de tenant inválido: '{tenant_name}'")

    # Idempotência: retorna tenant existente se schema já existe
    tenant, created = Customer.objects.get_or_create(
        schema_name=schema_name,
        defaults={"name": tenant_name},
    )

    if created:
        # Migrar schema recém-criado
        with tenant_context(tenant):
            call_command(
                "migrate_schemas",
                schema_name=tenant.schema_name,
                interactive=False,
                verbosity=0,
            )

    # Criar domínio primário se não existir
    base_domain = f"{schema_name}.{primary_domain_suffix}"
    domain_value = _ensure_unique_domain(base_domain)
    domain, _ = Domain.objects.get_or_create(
        domain=domain_value,
        defaults={"tenant": tenant, "is_primary": True},
    )

    return tenant, domain


def run_new_customer_schema_and_langflow_provision(schema_name: str, customer_pk: int) -> None:
    """
    Pós-criação de Customer: cria schema PostgreSQL do tenant e project Langflow.

    Corre tipicamente numa thread de fundo (ver signals). Erros são logados.
    """
    from api.services.langflow_workspace import provision_tenant_langflow_project

    try:
        instance = Customer.objects.get(pk=customer_pk)
        instance.auto_create_schema = True
        instance.save(update_fields=[])
        instance.auto_create_schema = False
        logger.info("Schema provisionado para tenant: %s", schema_name)

        instance.refresh_from_db()
        if instance.langflow_workspace_id:
            return

        project_id, lf_err = async_to_sync(provision_tenant_langflow_project)(
            tenant_schema=instance.schema_name,
            tenant_name=instance.name or instance.schema_name,
        )
        if lf_err:
            logger.error(
                "Langflow tenant project não provisionado para %s: %s",
                schema_name,
                lf_err,
            )
            return

        Customer.objects.filter(pk=customer_pk).update(
            langflow_workspace_id=project_id,
        )
    except Exception:
        logger.exception(
            "Falha ao provisionar schema/Langflow para tenant %s (pk=%s)",
            schema_name,
            customer_pk,
        )
