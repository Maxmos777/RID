"""Shared pytest fixtures for backend tests."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.asgi import application


@pytest.fixture
def asgi_app():
    return application


@pytest_asyncio.fixture
async def client(asgi_app):
    transport = ASGITransport(app=asgi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c
