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
async def test_provision_missing_api_key(settings) -> None:
    """Sem API key configurada → retorna erro de configuração, sem crash."""
    settings.LANGFLOW_SUPERUSER_API_KEY = None
    pid, err = await provision_tenant_langflow_project(
        tenant_schema="acme",
        tenant_name="Acme",
    )
    assert pid == ""
    assert err is not None
    assert "LANGFLOW_SUPERUSER_API_KEY" in err


@pytest.mark.asyncio
async def test_provision_tenant_langflow_project_success(settings) -> None:
    """Fluxo completo: criar user → activar → login → project."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-api-key"
    project_uuid = "550e8400-e29b-41d4-a716-446655440000"
    user_uuid = "61cb4f8a-48c1-4fdf-8355-e1af01e08506"
    calls: list[tuple[str, str]] = []

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        calls.append(("POST", path))
        if path in ("/api/v1/users/",):
            return httpx.Response(201, json={"id": user_uuid, "is_active": False, "username": "u"})
        if path in ("/api/v1/login",):
            return httpx.Response(200, json={"access_token": "jwt", "token_type": "bearer"})
        if path in ("/api/v1/projects/",):
            return httpx.Response(201, json={"id": project_uuid, "name": "rid-acme"})
        raise AssertionError(f"unexpected POST {path!r}")

    async def fake_patch(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        calls.append(("PATCH", path))
        assert f"/api/v1/users/{user_uuid}" in path
        assert kwargs.get("json") == {"is_active": True}
        return httpx.Response(200, json={"id": user_uuid, "is_active": True})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post
    mock_client.patch.side_effect = fake_patch

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="acme",
            tenant_name="Acme",
        )

    assert err is None
    assert pid == project_uuid
    # POST: users + login + projects = 3; PATCH: activate = 1
    assert mock_client.post.await_count == 3
    assert mock_client.patch.await_count == 1


@pytest.mark.asyncio
async def test_provision_existing_user_400_skips_activation(settings) -> None:
    """Utilizador já existe (400) → salta criação/activação, vai para login."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-api-key"
    project_uuid = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path in ("/api/v1/users/",):
            return httpx.Response(400, json={"detail": "Username already exists"})
        if path in ("/api/v1/login",):
            return httpx.Response(200, json={"access_token": "jwt", "token_type": "bearer"})
        if path in ("/api/v1/projects/",):
            return httpx.Response(201, json={"id": project_uuid, "name": "rid-beta"})
        raise AssertionError(f"unexpected POST {path!r}")

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post
    mock_client.patch.side_effect = AssertionError("PATCH should NOT be called when user exists")

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="beta",
            tenant_name="Beta",
        )

    assert err is None
    assert pid == project_uuid
    assert mock_client.patch.await_count == 0


@pytest.mark.asyncio
async def test_provision_activate_user_failure(settings) -> None:
    """Falha na activação do utilizador retorna erro."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-api-key"
    user_uuid = "61cb4f8a-48c1-4fdf-8355-e1af01e08506"

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path in ("/api/v1/users/",):
            return httpx.Response(201, json={"id": user_uuid, "is_active": False})
        raise AssertionError(f"unexpected POST {path!r}")

    async def fake_patch(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post
    mock_client.patch.side_effect = fake_patch

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="gamma",
            tenant_name="Gamma",
        )

    assert pid == ""
    assert err is not None
    assert "activate user failed" in err


@pytest.mark.asyncio
async def test_provision_login_failure(settings) -> None:
    """Falha no login retorna erro."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-api-key"
    user_uuid = "61cb4f8a-48c1-4fdf-8355-e1af01e08507"

    async def fake_post(url: str, **kwargs: object) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path in ("/api/v1/users/",):
            return httpx.Response(201, json={"id": user_uuid, "is_active": False})
        return httpx.Response(401, text="Incorrect username or password")

    async def fake_patch(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"id": user_uuid, "is_active": True})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post
    mock_client.patch.side_effect = fake_patch

    with patch("api.services.langflow_workspace.httpx.AsyncClient", return_value=mock_client):
        pid, err = await provision_tenant_langflow_project(
            tenant_schema="delta",
            tenant_name="Delta",
        )

    assert pid == ""
    assert err is not None
    assert "login failed" in err
