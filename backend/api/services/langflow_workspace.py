"""
Langflow tenant project provisioning (Langflow 1.8.3).

Spike (upstream v1.8.3): não existe /api/v1/workspaces/. Pastas = *projects*
(`POST /api/v1/projects/`), por utilizador (`Folder.user_id`).

Estratégia RID: um *utilizador de serviço* por tenant (`rid.svc.<schema>@tenant.rid`)
com password derivada (nunca mostrada a humanos). Esse utilizador possui um
project nomeado `rid-<schema>` onde flows partilhados do tenant podem viver.

O campo `Customer.langflow_workspace_id` guarda o UUID desse Folder (project).

Fluxo validado contra Langflow 1.8.3:
  1. POST /api/v1/users/          [x-api-key: SUPERUSER_API_KEY]  → cria user inactivo
  2. PATCH /api/v1/users/{id}     [x-api-key: SUPERUSER_API_KEY]  → activa user
  3. POST /api/v1/login           [form-data]                      → token serv user
  4. POST /api/v1/projects/       [Bearer token]                   → project/workspace

Se user já existe (400) → salta criação/activação, vai para login directamente.
"""
from __future__ import annotations

import hashlib
import logging
from uuid import UUID

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def tenant_service_username(schema_name: str) -> str:
    """Username único no Langflow para o tenant (registo público /api/v1/users/)."""
    safe = schema_name.replace("@", "_at_")[:48]
    return f"rid.svc.{safe}@tenant.rid"


def derive_tenant_service_password(schema_name: str) -> str:
    """Password determinística do utilizador de serviço Langflow (nunca mostrada a humanos)."""
    raw = f"{schema_name}:rid-lf-tenant-svc-v1:{settings.SECRET_KEY[:16]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _project_name_for_schema(schema_name: str) -> str:
    return f"rid-{schema_name}"[:255]


async def provision_tenant_langflow_project(
    *,
    tenant_schema: str,
    tenant_name: str,
) -> tuple[str, str | None]:
    """
    Garante utilizador de serviço Langflow + project (Folder) para o tenant.

    Returns (project_id_str, None) on success, ("", error_message) on failure.

    Falha silenciosa: erros são retornados como mensagem, nunca levantam excepção.
    O caller (services.py) decide se loga ou propaga.
    """
    api_key: str | None = getattr(settings, "LANGFLOW_SUPERUSER_API_KEY", None)
    if not api_key:
        return "", "LANGFLOW_SUPERUSER_API_KEY not configured — workspace não provisionado"

    username = tenant_service_username(tenant_schema)
    password = derive_tenant_service_password(tenant_schema)
    base = settings.LANGFLOW_BASE_URL.rstrip("/")
    superuser_headers = {"x-api-key": api_key}

    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        # ── 1. Criar utilizador de serviço (requer auth de superuser) ──────────
        create_resp = await client.post(
            "/api/v1/users/",
            json={"username": username, "password": password},
            headers=superuser_headers,
        )
        user_already_exists = create_resp.status_code == 400
        if not user_already_exists and create_resp.status_code not in (200, 201):
            return "", (
                f"langflow create service user failed: {create_resp.status_code} — "
                f"{create_resp.text}"
            )

        # ── 2. Activar utilizador (Langflow cria com is_active=false por defeito) ─
        if not user_already_exists:
            user_id: str = create_resp.json().get("id", "")
            if not user_id:
                return "", "langflow create user returned no id"
            patch_resp = await client.patch(
                f"/api/v1/users/{user_id}",
                json={"is_active": True},
                headers=superuser_headers,
            )
            if patch_resp.status_code not in (200, 201):
                return "", (
                    f"langflow activate user failed: {patch_resp.status_code} — "
                    f"{patch_resp.text}"
                )

        # ── 3. Login como utilizador de serviço ─────────────────────────────────
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": username, "password": password},
        )
        if login_resp.status_code != 200:
            return "", (
                f"langflow service user login failed: {login_resp.status_code} — "
                f"{login_resp.text}"
            )
        token: str = login_resp.json().get("access_token", "")
        if not token:
            return "", "langflow login returned no access_token"

        # ── 4. Criar project (workspace isolado do tenant) ──────────────────────
        proj_resp = await client.post(
            "/api/v1/projects/",
            json={
                "name": _project_name_for_schema(tenant_schema),
                "description": tenant_name or tenant_schema,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if proj_resp.status_code not in (200, 201):
            return "", (
                f"langflow create project failed: {proj_resp.status_code} — "
                f"{proj_resp.text}"
            )

        raw_id = proj_resp.json().get("id")
        if raw_id is None:
            return "", "langflow create project returned no id"

    try:
        UUID(str(raw_id))
    except ValueError:
        return "", f"langflow project id is not a UUID: {raw_id!r}"

    logger.info(
        "Langflow tenant project provisioned schema=%s project_id=%s",
        tenant_schema,
        raw_id,
    )
    return str(raw_id), None
