"""Tests for FastAPI tenant dependency — validação de entrada e comportamento."""
from __future__ import annotations

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_empty_host_raises_400():
    """Host vazio deve retornar 400, não 404."""
    from api.deps import get_current_tenant

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="")

    assert exc_info.value.status_code == 400
    assert "Host header is required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_whitespace_host_raises_400():
    """Host com apenas espaços deve retornar 400."""
    from api.deps import get_current_tenant

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="   ")

    assert exc_info.value.status_code == 400
    assert "Host header is required" in exc_info.value.detail


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unknown_host_raises_404():
    """Domínio desconhecido deve retornar 404."""
    from api.deps import get_current_tenant

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="tenant-inexistente-xyz99.rid.localhost")

    assert exc_info.value.status_code == 404
    assert "Tenant not found" in exc_info.value.detail


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_port_stripped_from_host():
    """Host com porta deve ter a porta removida antes da query."""
    from api.deps import get_current_tenant

    # Com BD disponível: domínio com porta -> tira a porta -> busca apenas o hostname
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(host="tenant-inexistente.rid.localhost:8080")

    # Deve ser 404 (tenant não encontrado), não 400 (host vazio)
    assert exc_info.value.status_code == 404
