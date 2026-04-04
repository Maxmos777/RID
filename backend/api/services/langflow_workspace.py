"""
Langflow tenant project provisioning (Langflow 1.8.3).

Spike (upstream v1.8.3): não existe /api/v1/workspaces/. Pastas = *projects*
(`POST /api/v1/projects/`), por utilizador (`Folder.user_id`).

Estratégia RID: um *utilizador de serviço* por tenant (`rid.svc.<schema>@tenant.rid`)
com password derivada (nunca mostrada a humanos). Esse utilizador possui um
project nomeado `rid-<schema>` onde flows partilhados do tenant podem viver.

O campo `Customer.langflow_workspace_id` guarda o UUID desse Folder (project).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import UUID

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def tenant_service_username(schema_name: str) -> str:
    """Username único no Langflow para o tenant (registo público /api/v1/users/)."""
    safe = schema_name.replace("@", "_at_")[:48]
    return f"rid.svc.{safe}@tenant.rid"


def _derive_tenant_service_password(schema_name: str) -> str:
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
    """
    username = tenant_service_username(tenant_schema)
    password = _derive_tenant_service_password(tenant_schema)
    base = settings.LANGFLOW_BASE_URL.rstrip("/")

    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        create_resp = await client.post(
            "/api/v1/users/",
            json={"username": username, "password": password},
        )
        if create_resp.status_code not in (200, 201, 400):
            return "", (
                f"langflow create service user failed: {create_resp.status_code} — "
                f"{create_resp.text}"
            )

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

        headers = {"Authorization": f"Bearer {token}"}
        body: dict[str, Any] = {
            "name": _project_name_for_schema(tenant_schema),
            "description": tenant_name or tenant_schema,
        }
        proj_resp = await client.post(
            "/api/v1/projects/",
            json=body,
            headers=headers,
        )
        if proj_resp.status_code not in (200, 201):
            return "", (
                f"langflow create project failed: {proj_resp.status_code} — "
                f"{proj_resp.text}"
            )

        data = proj_resp.json()
        raw_id = data.get("id")
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
