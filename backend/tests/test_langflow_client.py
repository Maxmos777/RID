"""
Unit tests para langflow_client — bridge Django Auth → Langflow.

Verifica:
- Auth usa API Key (x-api-key), não username+password
- Novo utilizador é activado após criação (PATCH is_active=True)
- user_id (UUID Langflow) é retornado no resultado
- Utilizador já existente (400) salta activação
- Re-login em cache não cria duplicado
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from api.services.langflow_client import get_or_create_langflow_user


# ─── helpers ────────────────────────────────────────────────────────────────

USER_UUID = "d014ea4d-8ac0-4b55-b662-e7078624dcb8"
PROJECT_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _make_mock_client(post_side_effect, patch_side_effect=None):
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    mock.post.side_effect = post_side_effect
    if patch_side_effect:
        mock.patch.side_effect = patch_side_effect
    else:
        mock.patch.return_value = httpx.Response(200, json={"id": USER_UUID, "is_active": True})
    return mock


# ─── tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_uses_api_key_header_not_password_login(settings) -> None:
    """Superuser auth deve usar x-api-key, não POST /api/v1/login com password."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-key"
    api_key_calls: list[dict] = []

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        headers = kwargs.get("headers", {})
        api_key_calls.append({"path": path, "headers": headers})

        if path == "/api/v1/users/":
            return httpx.Response(201, json={"id": USER_UUID, "is_active": False, "username": "u"})
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt", "token_type": "bearer"})
        if path == "/api/v1/api_key/":
            return httpx.Response(201, json={"api_key": "sk-test"})
        raise AssertionError(f"unexpected POST {path!r}")

    mock_client = _make_mock_client(fake_post)
    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_or_create_langflow_user("user@test.com", "password123")

    assert err is None
    # Deve ter apenas 1 chamada a /api/v1/login (utilizador pessoal), não 2
    # (o método antigo fazia login superuser + login utilizador = 2 chamadas)
    login_calls = [c for c in api_key_calls if c["path"] == "/api/v1/login"]
    assert len(login_calls) == 1, (
        f"Deve haver apenas 1 chamada a /api/v1/login (utilizador pessoal), "
        f"não login de superuser. Chamadas: {login_calls}"
    )

    # POST /api/v1/users/ deve ter x-api-key no header (superuser auth via API Key)
    user_creation_calls = [c for c in api_key_calls if c["path"] == "/api/v1/users/"]
    assert len(user_creation_calls) == 1
    assert "x-api-key" in user_creation_calls[0]["headers"], "x-api-key deve estar nos headers"


@pytest.mark.asyncio
async def test_new_user_activated_after_creation(settings) -> None:
    """Utilizador novo (201) deve ser activado via PATCH antes do login."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-key"
    patch_calls: list[str] = []

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path == "/api/v1/users/":
            return httpx.Response(201, json={"id": USER_UUID, "is_active": False})
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt"})
        if path == "/api/v1/api_key/":
            return httpx.Response(201, json={"api_key": "sk-test"})
        raise AssertionError(path)

    async def fake_patch(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        patch_calls.append(path)
        assert kwargs.get("json") == {"is_active": True}
        return httpx.Response(200, json={"id": USER_UUID, "is_active": True})

    mock_client = _make_mock_client(fake_post, fake_patch)
    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_or_create_langflow_user("user@test.com", "pass")

    assert err is None
    assert len(patch_calls) == 1
    assert USER_UUID in patch_calls[0], "PATCH deve conter o user_id"


@pytest.mark.asyncio
async def test_existing_user_skips_activation(settings) -> None:
    """Utilizador já existe (400) → salta PATCH de activação."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-key"

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path == "/api/v1/users/":
            return httpx.Response(400, json={"detail": "Username already exists"})
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt"})
        if path == "/api/v1/api_key/":
            return httpx.Response(201, json={"api_key": "sk-test"})
        raise AssertionError(path)

    mock_client = _make_mock_client(fake_post)
    mock_client.patch.side_effect = AssertionError("PATCH não deve ser chamado quando user existe")

    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_or_create_langflow_user("existing@test.com", "pass")

    assert err is None
    assert mock_client.patch.await_count == 0


@pytest.mark.asyncio
async def test_user_id_returned_in_result(settings) -> None:
    """Resultado deve incluir user_id (UUID do Langflow)."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-key"

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path == "/api/v1/users/":
            return httpx.Response(201, json={"id": USER_UUID, "is_active": False})
        if path == "/api/v1/login":
            return httpx.Response(200, json={"access_token": "jwt"})
        if path == "/api/v1/api_key/":
            return httpx.Response(201, json={"api_key": "sk-test"})
        raise AssertionError(path)

    mock_client = _make_mock_client(fake_post)
    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_or_create_langflow_user("user@test.com", "pass")

    assert err is None
    assert result.get("user_id") == USER_UUID, "user_id deve estar no resultado"
    assert result.get("access_token") == "jwt"
    assert result.get("api_key") == "sk-test"


@pytest.mark.asyncio
async def test_missing_api_key_returns_error(settings) -> None:
    """Sem LANGFLOW_SUPERUSER_API_KEY → retorna erro, sem crash."""
    settings.LANGFLOW_SUPERUSER_API_KEY = None

    result, err = await get_or_create_langflow_user("user@test.com", "pass")

    assert result == {}
    assert err is not None
    assert "LANGFLOW_SUPERUSER_API_KEY" in err


@pytest.mark.asyncio
async def test_login_failure_returns_error(settings) -> None:
    """Falha no login do utilizador retorna tuple de erro."""
    settings.LANGFLOW_SUPERUSER_API_KEY = "test-key"

    async def fake_post(url: str, **kwargs) -> httpx.Response:
        path = httpx.URL(url).path if "://" in url else url
        if path == "/api/v1/users/":
            return httpx.Response(201, json={"id": USER_UUID, "is_active": False})
        return httpx.Response(401, text="Incorrect username or password")

    mock_client = _make_mock_client(fake_post)
    with patch("api.services.langflow_client.httpx.AsyncClient", return_value=mock_client):
        result, err = await get_or_create_langflow_user("user@test.com", "wrong")

    assert result == {}
    assert err is not None
    assert "login failed" in err
