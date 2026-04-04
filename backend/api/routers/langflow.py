"""
Langflow API router — placeholder.

As rotas serão implementadas quando o RockLangflowClient for portado.
Ver: 2026-04-03-rid-platform-architecture.md — Phase Langflow Integration.

Padrão a seguir (do RockItDown):
  - Todas as views herdam de BaseLangflowMixin (api/langflow_mixin.py)
  - Usam TenantSchema como dependency para resolver o tenant
  - Executam operações de DB dentro de sync_to_async ou tenant_context
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/langflow", tags=["langflow"])


@router.get("/health")
async def langflow_health() -> dict:
    """Health check da integração Langflow — placeholder até o cliente ser portado."""
    return {
        "status": "not_implemented",
        "message": "Langflow integration pending — see rid-platform-architecture.md",
    }
