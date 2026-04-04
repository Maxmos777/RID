"""Integration tests for the health endpoint — no DB required."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_response_is_json(client):
    response = await client.get("/api/health")
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_api_prefix_routes_to_fastapi_not_django(client):
    """Garante que /api/ vai para FastAPI (JSON), não para Django (HTML)."""
    response = await client.get("/api/health")
    assert "application/json" in response.headers["content-type"]
    assert "<html" not in response.text
