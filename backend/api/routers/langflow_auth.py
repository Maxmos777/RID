"""
Langflow auto-login router.

GET /api/v1/langflow/auth/auto-login
  → requer Django session auth (AuthenticatedUser)
  → cria ou obtém utilizador Langflow para o utilizador Django
  → devolve JWT + api_key ao frontend
  → frontend guarda tokens em cookies httpOnly

Este é o padrão de bridge auto-login do RockItDown, adaptado para:
  - TenantUser (utilizadores no schema público — ADR-002)
  - UUID como pk do utilizador
  - async puro via httpx (sem sync_to_async no router)
"""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from asgiref.sync import sync_to_async

from api.deps import AuthenticatedUser
from api.services.langflow_client import get_or_create_langflow_user

router = APIRouter()


class AutoLoginResponse(BaseModel):
    access_token: str
    api_key: str


def _derive_langflow_password(user_id: str) -> str:
    """
    Deriva deterministicamente uma password Langflow a partir do UUID do utilizador Django.

    Usa SHA-256 para gerar uma password estável entre requests mas
    nunca armazenada em texto simples. O sufixo 'rid-lf-v1' é o
    namespace da versão — mudar invalida todas as passwords existentes.
    """
    raw = f"{user_id}:rid-lf-v1"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.get("/auth/auto-login", response_model=AutoLoginResponse)
async def auto_login(current_user: AuthenticatedUser) -> AutoLoginResponse:
    """
    Bridge endpoint: troca sessão Django por credenciais Langflow.

    Fluxo:
      1. Verificar se já existem credenciais Langflow em cache (TenantUser)
      2. Se sim: re-login para JWT fresco (JWT expira, API key não)
      3. Se não: criar utilizador Langflow e persistir credenciais
    """
    # TenantUser IS the user model (extends AbstractUser) — acesso directo
    langflow_email = current_user.email
    langflow_password = _derive_langflow_password(str(current_user.pk))

    if current_user.langflow_api_key and current_user.langflow_user_id:
        # Credenciais em cache — re-login apenas para JWT fresco
        result, err = await get_or_create_langflow_user(langflow_email, langflow_password)
        if err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Langflow unavailable: {err}",
            )
        return AutoLoginResponse(
            access_token=result["access_token"],
            api_key=current_user.langflow_api_key,
        )

    # Primeira vez: criar + persistir
    result, err = await get_or_create_langflow_user(langflow_email, langflow_password)
    if err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Langflow unavailable: {err}",
        )

    # Persistir credenciais no TenantUser via sync_to_async (ADR-001 — thread safety)
    def _save_credentials(user, api_key: str) -> None:
        user.langflow_api_key = api_key
        user.langflow_user_id = None  # UUID preenchido futuramente via whoami
        user.save(update_fields=["langflow_api_key", "langflow_user_id"])

    await sync_to_async(_save_credentials, thread_sensitive=True)(
        current_user, result.get("api_key", "")
    )

    return AutoLoginResponse(
        access_token=result["access_token"],
        api_key=current_user.langflow_api_key,
    )
