"""
BaseLangflowMixin para rotas FastAPI com integração Langflow.

Origem: RockItDown/src/rocklangflow/views.py:378-403 (adaptado para FastAPI).
Diferença: usa FastAPI Request em vez de Django HttpRequest.

Roadmap de implementação:
  Fase 1 (agora): mixin com get_tenant_user_uuid + get_client placeholder
  Fase 2 (próxima task): implementar get_client com RockLangflowClient portado
  Fase 3 (futuro): JWT dependency para request.user no FastAPI
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseLangflowMixin:
    """
    Mixin base para endpoints FastAPI que chamam o Langflow.

    Responsabilidades:
      - Extrair o UUID do utilizador tenant do header ou do utilizador autenticado
      - Criar o cliente Langflow com o UUID correcto

    Uso:
        class MyEndpoint(BaseLangflowMixin):
            async def handle(self, request: Request, schema: TenantSchema):
                uuid = self.get_tenant_user_uuid(request)
                if not uuid:
                    raise HTTPException(status_code=403, detail="UUID não encontrado")
                client = await self.get_client(uuid)
                ...
    """

    def get_tenant_user_uuid(self, request) -> Optional[str]:
        """
        Extrai UUID do utilizador tenant.

        Prioridade:
          1. Header X-Tenant-User-UUID (para chamadas M2M entre serviços)
          2. request.user.langflow_user_id (campo em TenantUser)
          3. str(request.user.id) como fallback de desenvolvimento
        """
        # FastAPI não tem request.user nativo — será injectado via dependency JWT
        # quando a autenticação for implementada (ver rid-platform-architecture.md)
        uuid_header = getattr(request, "headers", {}).get("x-tenant-user-uuid")
        if uuid_header:
            return uuid_header

        user = getattr(request, "user", None)
        if user is not None:
            langflow_id = getattr(user, "langflow_user_id", None)
            if langflow_id:
                return str(langflow_id)
            user_id = getattr(user, "id", None)
            if user_id:
                return str(user_id)

        return None

    async def get_client(self, tenant_user_uuid: str):
        """
        Retorna cliente Langflow configurado para o tenant.

        NotImplementedError intencional: o RockLangflowClient ainda não foi portado.
        Implementar quando a task de integração Langflow for executada
        (ver 2026-04-03-rid-platform-architecture.md — Phase Langflow Integration).
        """
        raise NotImplementedError(
            "get_client() requer RockLangflowClient portado. "
            "Ver plano de arquitectura: Phase Langflow Integration."
        )
