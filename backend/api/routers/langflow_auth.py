"""
Langflow auto-login router.

GET /api/langflow/auth/auto-login
  → requer Django session auth (AuthenticatedUser)
  → cria ou obtém utilizador Langflow para o utilizador Django
  → devolve JWT + api_key ao frontend
  → frontend guarda tokens em cookies httpOnly

Bridge pattern: Django session → credenciais Langflow pessoais.
  - Primeira visita: cria conta Langflow, activa, obtém JWT + API key
  - Visitas seguintes: re-login para JWT fresco (API key em cache)

ADR-001: sync_to_async thread_sensitive=True para ORM em contexto async
ADR-002: utilizadores no schema público (TenantUser)
ADR-009: auth Langflow via API Key (x-api-key), não via password superuser
"""
from __future__ import annotations

import hashlib
import uuid

from asgiref.sync import sync_to_async
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.deps import AuthenticatedUser
from api.services.langflow_client import get_or_create_langflow_user

router = APIRouter()


class AutoLoginResponse(BaseModel):
    access_token: str
    api_key: str
    langflow_user_id: str | None = None


def _derive_langflow_password(user_id: str) -> str:
    """
    Deriva deterministicamente uma password Langflow a partir do UUID do utilizador Django.

    Usa SHA-256 para gerar uma password estável entre requests mas
    nunca armazenada em texto simples. O sufixo 'rid-lf-v1' é o
    namespace da versão — mudar invalida todas as passwords existentes.
    """
    raw = f"{user_id}:rid-lf-v1"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _save_langflow_credentials(user, api_key: str, user_id: str) -> None:
    """Persiste credenciais Langflow no TenantUser. Corre em thread dedicada (ADR-001)."""
    changed_fields: list[str] = []
    if api_key and user.langflow_api_key != api_key:
        user.langflow_api_key = api_key
        changed_fields.append("langflow_api_key")
    if user_id:
        try:
            parsed_id = uuid.UUID(user_id)
            if user.langflow_user_id != parsed_id:
                user.langflow_user_id = parsed_id
                changed_fields.append("langflow_user_id")
        except ValueError:
            pass
    if changed_fields:
        user.save(update_fields=changed_fields)


@router.get("/auth/auto-login", response_model=AutoLoginResponse)
async def auto_login(current_user: AuthenticatedUser) -> AutoLoginResponse:
    """
    Bridge endpoint: troca sessão Django por credenciais Langflow pessoais.

    Fluxo:
      1. Se credenciais em cache (TenantUser.langflow_api_key) → re-login para JWT fresco
      2. Se não → criar conta Langflow, activar, persistir user_id + api_key
    """
    langflow_username = current_user.email
    langflow_password = _derive_langflow_password(str(current_user.pk))

    result, err = await get_or_create_langflow_user(langflow_username, langflow_password)
    if err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Langflow unavailable: {err}",
        )

    returned_user_id: str = result.get("user_id", "")
    returned_api_key: str = result.get("api_key", "")

    # Persistir credenciais novas (ou actualizar se mudaram) — ADR-001
    if returned_api_key or returned_user_id:
        await sync_to_async(_save_langflow_credentials, thread_sensitive=True)(
            current_user,
            returned_api_key,
            returned_user_id,
        )

    # Usar api_key em cache se Langflow não devolveu uma nova (user já existia)
    final_api_key = returned_api_key or (current_user.langflow_api_key or "")
    final_user_id = returned_user_id or (
        str(current_user.langflow_user_id) if current_user.langflow_user_id else None
    )

    access_token: str = result.get("access_token", "")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Langflow returned no access_token",
        )

    return AutoLoginResponse(
        access_token=access_token,
        api_key=final_api_key,
        langflow_user_id=final_user_id,
    )
