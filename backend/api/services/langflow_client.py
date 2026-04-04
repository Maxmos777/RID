"""
Langflow HTTP client — bridge Django Auth → Langflow.

Wraps Langflow 1.8.3 REST API:
  POST  /api/v1/users/         → criar utilizador Langflow (requer x-api-key superuser)
  PATCH /api/v1/users/{id}     → activar utilizador (is_active=true; Langflow cria inactivo)
  POST  /api/v1/login          → login do utilizador (form-data) → JWT pessoal
  POST  /api/v1/api_key/       → criar API key pessoal do utilizador

Auth de superuser: x-api-key (LANGFLOW_SUPERUSER_API_KEY) em vez de login com password.
Isto é consistente com langflow_workspace.py e não depende de LANGFLOW_AUTO_LOGIN.

Todas as funções retornam (result, error) — sem excepções propagadas.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


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
            return {}, f"create user failed: {create_resp.status_code} — {create_resp.text}"

        user_id: str = ""
        if not user_already_exists:
            user_id = create_resp.json().get("id", "")

        # ── 2. Activar utilizador (apenas se recém-criado) ────────────────────
        if not user_already_exists and user_id:
            patch_resp = await client.patch(
                f"/api/v1/users/{user_id}",
                json={"is_active": True},
                headers=superuser_headers,
            )
            if patch_resp.status_code not in (200, 201):
                return {}, f"activate user failed: {patch_resp.status_code} — {patch_resp.text}"

        # ── 3. Login como utilizador → JWT pessoal ────────────────────────────
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": email, "password": password},
        )
        if login_resp.status_code != 200:
            return {}, f"user login failed: {login_resp.status_code} — {login_resp.text}"

        user_token: str = login_resp.json().get("access_token", "")
        if not user_token:
            return {}, "login returned no access_token"

        # ── 4. Criar / obter API key pessoal ──────────────────────────────────
        key_resp = await client.post(
            "/api/v1/api_key/",
            json={"name": "rid-auto"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        personal_api_key = ""
        if key_resp.status_code in (200, 201):
            personal_api_key = key_resp.json().get("api_key", "")

    logger.info("Langflow user provisioned email=%s user_id=%s", email, user_id or "existing")
    return {
        "access_token": user_token,
        "api_key": personal_api_key,
        "user_id": user_id,
    }, None
