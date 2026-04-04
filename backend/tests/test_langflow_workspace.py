"""Unit tests for Langflow tenant project provisioning (mocked httpx)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from api.services.langflow_workspace import (
    provision_tenant_langflow_project,
    tenant_service_username,
)


@pytest.mark.asyncio
async def test_tenant_service_username_stable() -> None:
    assert tenant_service_username("acme_corp") == "rid.svc.acme_corp@tenant.rid"


@pytest.mark.asyncio
async def test_provision_tenant_langflow_project_success() -> None:
    project_uuid = "550e8400-e29b-41d4-a716-446655440000"

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path.endswith("/api/v1/users/") or path == "/api/v1/users/":
            return httpx.Response(201, json={"username": "u"})
        if path.endswith("/api/v1/login") or path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt"})
        if path.endswith("/api/v1/projects/") or path == "/api/v1/projects/":
            return httpx.Response(201, json={"id": project_uuid, "name": "rid-acme"})
        raise AssertionError(f"unexpected post {path!r}")

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="acme",
            tenant_name="Acme",
        )

    assert err is None
    assert pid == project_uuid
    assert mock_client.post.await_count == 3


@pytest.mark.asyncio
async def test_provision_existing_user_400_still_logs_in() -> None:
    project_uuid = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    calls: list[str] = []

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        calls.append(path)
        if "/api/v1/users/" in path or path.endswith("users/"):
            return httpx.Response(400, json={"detail": "unavailable"})
        if "login" in path:
            return httpx.Response(200, json={"access_token": "jwt"})
        if "projects" in path:
            return httpx.Response(201, json={"id": project_uuid, "name": "x"})
        raise AssertionError(path)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="beta",
            tenant_name="Beta",
        )

    assert err is None
    assert pid == project_uuid


@pytest.mark.asyncio
async def test_provision_login_failure() -> None:
    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if "users" in path:
            return httpx.Response(201, json={})
        return httpx.Response(401, text="nope")

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="gamma",
            tenant_name="G",
        )

    assert pid == ""
    assert err is not None
    assert "login failed" in err
