"""
Langflow auto-login router (Opção C: credenciais do utilizador de serviço por tenant).

GET /api/v1/langflow/auth/auto-login
  → requer Django session auth (AuthenticatedUser)
  → resolve tenant (Host ou ?tenant_schema=)
  → verifica TenantMembership
  → exige Customer.langflow_workspace_id provisionado (409 se ausente)
  → devolve JWT + api_key do serviço + workspace_id

ADR-001: sync_to_async thread_sensitive=True para ORM em contexto async
ADR-002: utilizadores no schema público (TenantUser)
ADR-009: auth Langflow via API Key (x-api-key), não via password superuser
"""
from __future__ import annotations

from typing import Annotated, Any

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.deps import AuthenticatedUser
from api.services.langflow_client import get_tenant_service_credentials

router = APIRouter()


class AutoLoginResponse(BaseModel):
    access_token: str
    api_key: str
    workspace_id: str = Field(
        ...,
        description="UUID do project Langflow (Folder) do tenant.",
    )
    langflow_user_id: str | None = Field(
        None,
        description="Deprecated: bridge por utilizador de serviço; sempre null.",
    )


def _bridge_context_sync(
    user,
    host_header: str,
    tenant_schema_query: str | None,
) -> tuple[str, Any]:
    from django.db import connection

    from apps.accounts.models import TenantMembership
    from apps.tenants.models import Customer, Domain

    if tenant_schema_query is not None and tenant_schema_query.strip() != "":
        schema = tenant_schema_query.strip()
        if not TenantMembership.objects.filter(
            user=user,
            tenant_schema=schema,
            is_active=True,
        ).exists():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this tenant",
            )
        try:
            tenant = Customer.objects.get(schema_name=schema)
        except Customer.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )
        connection.set_tenant(tenant)
        return schema, tenant

    hostname = host_header.split(":")[0].strip()
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host header is required",
        )
    try:
        domain = Domain.objects.select_related("tenant").get(domain=hostname)
    except Domain.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found for domain: {hostname}",
        )
    tenant = domain.tenant
    schema = tenant.schema_name

    active_qs = TenantMembership.objects.filter(user=user, is_active=True)
    count = active_qs.count()
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of any tenant",
        )
    if count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "tenant_schema query parameter is required when the user belongs "
                "to multiple tenants"
            ),
        )
    if not active_qs.filter(tenant_schema=schema).exists():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this tenant",
        )
    connection.set_tenant(tenant)
    return schema, tenant


def _persist_service_api_key(customer_pk: int, api_key: str) -> None:
    from apps.tenants.models import Customer

    Customer.objects.filter(pk=customer_pk).update(langflow_service_api_key=api_key)


@router.get("/auth/auto-login", response_model=AutoLoginResponse)
async def auto_login(
    current_user: AuthenticatedUser,
    host: Annotated[str, Header()] = "",
    tenant_schema: str | None = Query(None, alias="tenant_schema"),
) -> AutoLoginResponse:
    """
    Bridge: sessão Django → credenciais Langflow do utilizador de serviço do tenant.
    """
    await sync_to_async(current_user.refresh_from_db, thread_sensitive=True)()

    schema_name, customer = await sync_to_async(
        _bridge_context_sync,
        thread_sensitive=True,
    )(current_user, host, tenant_schema)

    await sync_to_async(customer.refresh_from_db, thread_sensitive=True)()

    if customer.langflow_workspace_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Langflow workspace not provisioned for this tenant yet",
        )

    result, err = await get_tenant_service_credentials(
        schema_name,
        customer.langflow_service_api_key or None,
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Langflow unavailable: {err}",
        )

    access_token: str = result.get("access_token", "")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Langflow returned no access_token",
        )

    api_key: str = result.get("api_key", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Langflow returned no api_key",
        )

    if not customer.langflow_service_api_key:
        await sync_to_async(_persist_service_api_key, thread_sensitive=True)(
            customer.pk,
            api_key,
        )

    return AutoLoginResponse(
        access_token=access_token,
        api_key=api_key,
        workspace_id=str(customer.langflow_workspace_id),
        langflow_user_id=None,
    )
