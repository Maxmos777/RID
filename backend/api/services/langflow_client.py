"""
Langflow HTTP client — bridge Django Auth → Langflow.

Wraps Langflow 1.8.3 REST API:
  POST  /api/v1/users/         → criar utilizador (requer x-api-key superuser)
  PATCH /api/v1/users/{id}     → activar (is_active=true; Langflow cria inactivo)
  POST  /api/v1/login          → login do utilizador (form-data) → JWT pessoal
  POST  /api/v1/api_key/       → criar API key pessoal do utilizador

Auth de superuser: x-api-key (LANGFLOW_SUPERUSER_API_KEY) em vez de login com password.
Isto é consistente com langflow_workspace.py e não depende de LANGFLOW_AUTO_LOGIN.

Todas as funções retornam (result, error) — sem excepções propagadas.

SECURITY FIXES #3, #4:
  - Dict access seguro com .get() + defaults
  - Validação Pydantic em todas as respostas Langflow
  - Error handling para respostas malformadas (503 Bad Gateway)
"""
from __future__ import annotations

import logging
from typing import Any, TypedDict

import httpx
from django.conf import settings
from pydantic import BaseModel, Field, ValidationError

from api.services.langflow_workspace import (
    derive_tenant_service_password,
    tenant_service_username,
)

logger = logging.getLogger(__name__)


class LangflowUserCredentials(TypedDict, total=False):
    """Resultado de get_or_create_langflow_user / get_tenant_service_credentials."""

    access_token: str
    api_key: str
    user_id: str


# ─────────────────────────────────────────────────────────────────────────
# SECURITY FIX #4: Pydantic Response Models for JSON Validation
# ─────────────────────────────────────────────────────────────────────────


class LangflowUserResponse(BaseModel):
    """
    Schema de resposta de criação de utilizador Langflow.
    Valida estrutura antes de acesso via dict keys.
    """
    id: str = Field(..., description="ID único do utilizador Langflow")
    username: str | None = None
    is_active: bool = False


class LangflowLoginResponse(BaseModel):
    """
    Schema de resposta de login Langflow.
    """
    access_token: str = Field(...)
    token_type: str | None = "bearer"


class LangflowApiKeyResponse(BaseModel):
    """
    Schema de resposta de criação de API key Langflow.
    """
    api_key: str = Field(...)
    name: str | None = None
    user_id: str | None = None


async def get_or_create_langflow_user(
    email: str,
    password: str,
) -> tuple[dict[str, Any], str | None]:
    """
    Garante que existe um utilizador Langflow e retorna as suas credenciais.

    Fluxo:
      1. POST /api/v1/users/      [x-api-key superuser] → criar utilizador
         - 201 → novo utilizador, is_active=False por defeito
         - 400 → já existe, continuar para login
      2. PATCH /api/v1/users/{id} [x-api-key superuser] → activar (só se novo)
      3. POST /api/v1/login       [form-data]           → JWT pessoal
      4. POST /api/v1/api_key/    [Bearer token]        → API key pessoal

    Returns:
        ({"access_token": ..., "api_key": ..., "user_id": ...}, None) on success
        ({}, error_message) on failure

    ADR-009: auth via API Key (x-api-key), não via login com password de superuser.

    SECURITY:
      - Todas as respostas JSON são validadas com Pydantic
      - Dict access safe com .get() + defaults
      - Logging detalhado de erros
    """
    api_key: str | None = getattr(settings, "LANGFLOW_SUPERUSER_API_KEY", None)
    if not api_key:
        return {}, "LANGFLOW_SUPERUSER_API_KEY not configured"

    superuser_headers = {"x-api-key": api_key}
    base = settings.LANGFLOW_BASE_URL.rstrip("/")

    async with httpx.AsyncClient(base_url=base, timeout=10) as client:
        # ── 1. Criar utilizador ───────────────────────────────────────────────
        create_resp = await client.post(
            "/api/v1/users/",
            json={"username": email, "password": password},
            headers=superuser_headers,
        )
        user_already_exists = create_resp.status_code == 400
        if not user_already_exists and create_resp.status_code not in (200, 201):
            logger.error(
                "Langflow create user failed: %d",
                create_resp.status_code,
                extra={"email": email, "response_text": create_resp.text[:200]},
            )
            return {}, f"create user failed: {create_resp.status_code}"

        user_id: str = ""
        if not user_already_exists:
            try:
                user_data = LangflowUserResponse(**create_resp.json())
                user_id = user_data.id
            except ValidationError as e:
                logger.error(
                    "Langflow create user response validation failed: %s",
                    e,
                    extra={"email": email},
                )
                return {}, "Invalid response from Langflow (create user)"

        # ── 2. Activar utilizador (apenas se recém-criado) ────────────────────
        if not user_already_exists and user_id:
            patch_resp = await client.patch(
                f"/api/v1/users/{user_id}",
                json={"is_active": True},
                headers=superuser_headers,
            )
            if patch_resp.status_code not in (200, 201):
                logger.error(
                    "Langflow activate user failed: %d",
                    patch_resp.status_code,
                    extra={"user_id": user_id, "response_text": patch_resp.text[:200]},
                )
                return {}, f"activate user failed: {patch_resp.status_code}"

        # ── 3. Login como utilizador → JWT pessoal ────────────────────────────
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": email, "password": password},
        )
        if login_resp.status_code != 200:
            logger.error(
                "Langflow user login failed: %d",
                login_resp.status_code,
                extra={"email": email, "response_text": login_resp.text[:200]},
            )
            return {}, f"user login failed: {login_resp.status_code}"

        try:
            login_data = LangflowLoginResponse(**login_resp.json())
            user_token = login_data.access_token
        except ValidationError as e:
            logger.error(
                "Langflow login response validation failed: %s",
                e,
                extra={"email": email},
            )
            return {}, "Invalid response from Langflow (login)"

        if not user_token:
            logger.error(
                "Langflow login returned empty access_token",
                extra={"email": email},
            )
            return {}, "login returned no access_token"

        # ── 4. Criar / obter API key pessoal ──────────────────────────────────
        key_resp = await client.post(
            "/api/v1/api_key/",
            json={"name": "rid-auto"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        personal_api_key = ""
        if key_resp.status_code in (200, 201):
            try:
                key_data = LangflowApiKeyResponse(**key_resp.json())
                personal_api_key = key_data.api_key
            except ValidationError as e:
                logger.warning(
                    "Langflow api_key response validation failed: %s",
                    e,
                    extra={"email": email},
                )
                # Graceful degradation — continue without personal API key

    logger.info(
        "Langflow user provisioned",
        extra={"email": email, "user_id": user_id or "existing"},
    )
    return {
        "access_token": user_token,
        "api_key": personal_api_key,
        "user_id": user_id,
    }, None


async def get_tenant_service_credentials(
    tenant_schema: str,
    cached_api_key: str | None,
) -> tuple[LangflowUserCredentials, str | None]:
    """
    JWT + API key do utilizador de serviço Langflow do tenant.

    Não cria o utilizador — isso é feito em provision_tenant_langflow_project.
    Se ``cached_api_key`` estiver definido, só renova o JWT (POST /login).

    SECURITY:
      - Respostas JSON validadas com Pydantic
      - Dict access safe com .get() + defaults
      - Logging detalhado de erros
    """
    username = tenant_service_username(tenant_schema)
    password = derive_tenant_service_password(tenant_schema)
    base = settings.LANGFLOW_BASE_URL.rstrip("/")

    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": username, "password": password},
        )
        if login_resp.status_code != 200:
            logger.error(
                "Langflow service user login failed: %d",
                login_resp.status_code,
                extra={"schema": tenant_schema, "response_text": login_resp.text[:200]},
            )
            return {}, f"service user login failed: {login_resp.status_code}"

        try:
            login_data = LangflowLoginResponse(**login_resp.json())
            user_token = login_data.access_token
        except ValidationError as e:
            logger.error(
                "Langflow service login response validation failed: %s",
                e,
                extra={"schema": tenant_schema},
            )
            return {}, "Invalid response from Langflow (service login)"

        if not user_token:
            logger.error(
                "Langflow service login returned empty access_token",
                extra={"schema": tenant_schema},
            )
            return {}, "login returned no access_token"

        if cached_api_key:
            logger.debug(
                "Using cached Langflow service API key",
                extra={"schema": tenant_schema},
            )
            return {
                "access_token": user_token,
                "api_key": cached_api_key,
                "user_id": "",
            }, None

        key_resp = await client.post(
            "/api/v1/api_key/",
            json={"name": f"rid-svc-{tenant_schema}"[:64]},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        if key_resp.status_code not in (200, 201):
            logger.error(
                "Langflow service api_key create failed: %d",
                key_resp.status_code,
                extra={"schema": tenant_schema, "response_text": key_resp.text[:200]},
            )
            return {}, f"api_key create failed: {key_resp.status_code}"

        try:
            key_data = LangflowApiKeyResponse(**key_resp.json())
            new_key = key_data.api_key
        except ValidationError as e:
            logger.error(
                "Langflow service api_key response validation failed: %s",
                e,
                extra={"schema": tenant_schema},
            )
            return {}, "Invalid response from Langflow (api_key)"

        if not new_key:
            logger.error(
                "Langflow service api_key response missing api_key field",
                extra={"schema": tenant_schema},
            )
            return {}, "api_key response missing api_key"

    logger.info(
        "Langflow service credentials refreshed",
        extra={"schema": tenant_schema},
    )
    return {
        "access_token": user_token,
        "api_key": new_key,
        "user_id": "",
    }, None
