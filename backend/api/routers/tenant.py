"""
Tenant router — expõe informação do tenant activo ao frontend.

GET  /api/v1/tenants/current  → schema_name, domain, plan do tenant activo
POST /api/v1/tenants/         → cria novo tenant (onboarding — futuro)

O tenant activo é resolvido pela dependency TenantSchema (api/deps.py)
que usa sync_to_async para chamar connection.set_tenant (ADR-001).
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.deps import TenantSchema

router = APIRouter()


class TenantInfo(BaseModel):
    schema_name: str
    domain: str
    plan: str


@router.get("/current", response_model=TenantInfo)
async def current_tenant(schema_name: TenantSchema) -> TenantInfo:
    """
    Devolve o contexto do tenant activo para o request corrente.

    O schema_name é resolvido pelo header Host via TenantSchema dependency
    (ADR-001 — sync_to_async com thread_sensitive=True).
    """
    from asgiref.sync import sync_to_async

    def _get_tenant_info(schema: str) -> dict:
        from apps.tenants.models import Customer, Domain

        try:
            customer = Customer.objects.get(schema_name=schema)
            domain_obj = Domain.objects.filter(
                tenant=customer, is_primary=True
            ).first()
            return {
                "schema_name": schema,
                "domain": domain_obj.domain if domain_obj else schema,
                "plan": getattr(customer, "plan", "free"),
            }
        except Customer.DoesNotExist:
            return {"schema_name": schema, "domain": schema, "plan": "free"}

    info = await sync_to_async(_get_tenant_info, thread_sensitive=True)(schema_name)
    return TenantInfo(**info)
