"""Testes para get_tenant_service_credentials (utilizador de serviço por tenant)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from api.services.langflow_client import get_tenant_service_credentials


@pytest.mark.asyncio
async def test_service_credentials_with_cached_key_only_login(settings) -> None:
    """Com API key em cache: apenas POST /login, sem POST /api_key/."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "sup"
    posts: list[str] = []

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        posts.append(path)
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt-svc"})
        if path == "/api/v1/api_key/":
            raise AssertionError("api_key não deve ser chamado quando há cache")
        raise AssertionError(path)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_tenant_service_credentials("acme", "cached-key-123")

    assert err is None
    assert result["access_token"] == "jwt-svc"
    assert result["api_key"] == "cached-key-123"
    assert posts == ["/api/v1/login"]


@pytest.mark.asyncio
async def test_service_credentials_without_cache_creates_api_key(settings) -> None:
    """Sem cache: login + POST /api_key/."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "sup"

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt-svc"})
        if path == "/api/v1/api_key/":
            return httpx.Response(201, json={"api_key": "sk-new"})
        raise AssertionError(path)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_tenant_service_credentials("acme", None)

    assert err is None
    assert result["access_token"] == "jwt-svc"
    assert result["api_key"] == "sk-new"


@pytest.mark.asyncio
async def test_service_credentials_login_failure(settings) -> None:
    settings.LANGFLOW_SUPERUSER_API_KEY = "sup"

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        return httpx.Response(401, text="nope")

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = fake_post

    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_tenant_service_credentials("acme", None)

    assert result == {}
    assert err is not None
    assert "service user login failed" in err
