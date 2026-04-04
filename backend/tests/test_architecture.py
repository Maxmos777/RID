"""
ADR Compliance Tests — Architecture Guard

Verifica que as decisões documentadas nos ADRs continuam implementadas
no código. Corre automaticamente em cada `make test` e em CI.

Referência: docs/adr/README.md — ADR-001 a ADR-006
"""
from __future__ import annotations

from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# ADR-001: sync_to_async com thread_sensitive=True para isolamento de tenant
# Risco se violado: race condition silenciosa entre corrotinas no mesmo worker
# ---------------------------------------------------------------------------

def test_adr001_thread_sensitive_present():
    """ADR-001: sync_to_async deve usar thread_sensitive=True em api/deps.py."""
    src = (BASE_DIR / "api" / "deps.py").read_text()
    assert "thread_sensitive=True" in src, (
        "ADR-001 VIOLADO: thread_sensitive=True ausente em api/deps.py. "
        "Remover este argumento introduz race condition silenciosa em produção. "
        "Ver docs/adr/ADR-001-sync-to-async-tenant-isolation.md"
    )


def test_adr001_sync_to_async_wraps_resolve():
    """ADR-001: _resolve_tenant deve ser chamada via sync_to_async, não directamente."""
    src = (BASE_DIR / "api" / "deps.py").read_text()
    assert "sync_to_async(_resolve_tenant" in src, (
        "ADR-001 VIOLADO: _resolve_tenant não está envolvida por sync_to_async. "
        "Ver docs/adr/ADR-001-sync-to-async-tenant-isolation.md"
    )


def test_adr001_no_direct_async_orm_in_api():
    """ADR-001: Não deve haver chamadas ORM async directas em api/ (aget, asave, adelete)."""
    api_dir = BASE_DIR / "api"
    violations = []
    for py_file in api_dir.rglob("*.py"):
        src = py_file.read_text()
        for method in (".aget(", ".asave(", ".adelete(", ".aupdate("):
            if method in src:
                violations.append(f"{py_file.relative_to(BASE_DIR)}:{method}")

    assert not violations, (
        "ADR-001 VIOLADO: Chamadas ORM async directas encontradas em api/. "
        "Devem ser envolvidas por sync_to_async(thread_sensitive=True):\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# ADR-002: Utilizadores no schema público (SHARED_APPS), não no tenant
# Risco se violado: allauth quebra, migrações erradas, auth falha
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_adr002_accounts_in_shared_apps():
    """ADR-002: apps.accounts deve estar em SHARED_APPS."""
    from django.conf import settings
    assert "apps.accounts" in settings.SHARED_APPS, (
        "ADR-002 VIOLADO: apps.accounts não encontrado em SHARED_APPS. "
        "Ver docs/adr/ADR-002-users-in-public-schema.md"
    )


@pytest.mark.django_db
def test_adr002_accounts_not_in_tenant_apps():
    """ADR-002: apps.accounts NÃO deve estar em TENANT_APPS."""
    from django.conf import settings
    assert "apps.accounts" not in settings.TENANT_APPS, (
        "ADR-002 VIOLADO: apps.accounts encontrado em TENANT_APPS. "
        "Utilizadores no schema do tenant quebra allauth e auth multi-tenant. "
        "Ver docs/adr/ADR-002-users-in-public-schema.md"
    )


@pytest.mark.django_db
def test_adr002_tenant_user_extends_abstract_user():
    """ADR-002: TenantUser deve estender AbstractUser (schema público)."""
    from django.contrib.auth.models import AbstractUser
    from apps.accounts.models import TenantUser
    assert issubclass(TenantUser, AbstractUser), (
        "ADR-002 VIOLADO: TenantUser não extends AbstractUser. "
        "Ver docs/adr/ADR-002-users-in-public-schema.md"
    )


# ---------------------------------------------------------------------------
# ADR-003: Django + FastAPI ASGI híbrido com _API_PREFIX routing
# Risco se violado: /api sem barra vai para Django, FastAPI inacessível
# ---------------------------------------------------------------------------

def test_adr003_api_prefix_defined():
    """ADR-003: _API_PREFIX deve estar definido em core/asgi.py."""
    src = (BASE_DIR / "core" / "asgi.py").read_text()
    assert '_API_PREFIX = "/api"' in src, (
        "ADR-003 VIOLADO: _API_PREFIX não definido em core/asgi.py. "
        "Ver docs/adr/ADR-003-django-fastapi-hybrid-asgi.md"
    )


def test_adr003_routing_covers_api_without_slash():
    """ADR-003: routing deve cobrir /api (sem barra) e /api/* (com barra)."""
    src = (BASE_DIR / "core" / "asgi.py").read_text()
    assert "path == _API_PREFIX or path.startswith" in src, (
        "ADR-003 VIOLADO: routing não cobre /api sem trailing slash. "
        "Pedidos a /api vão para Django em vez de FastAPI. "
        "Ver docs/adr/ADR-003-django-fastapi-hybrid-asgi.md"
    )


def test_adr003_django_app_initialized_before_fastapi():
    """ADR-003: get_asgi_application() deve ser chamado antes de create_app()."""
    src = (BASE_DIR / "core" / "asgi.py").read_text()
    pos_django = src.find("get_asgi_application()")
    pos_fastapi = src.find("create_app()")
    assert pos_django != -1, "get_asgi_application() não encontrado em asgi.py"
    assert pos_fastapi != -1, "create_app() não encontrado em asgi.py"
    assert pos_django < pos_fastapi, (
        "ADR-003 VIOLADO: get_asgi_application() deve ser chamado ANTES de create_app(). "
        "Django setup deve preceder a inicialização do FastAPI. "
        "Ver docs/adr/ADR-003-django-fastapi-hybrid-asgi.md"
    )


# ---------------------------------------------------------------------------
# ADR-004: provision_tenant_for_user idempotente via get_or_create
# Risco se violado: provisioning falha em retry, duplica tenants
# ---------------------------------------------------------------------------

def test_adr004_get_or_create_in_services():
    """ADR-004: services.py deve usar get_or_create para idempotência."""
    src = (BASE_DIR / "apps" / "tenants" / "services.py").read_text()
    assert "get_or_create" in src, (
        "ADR-004 VIOLADO: get_or_create ausente em apps/tenants/services.py. "
        "Provisioning não é idempotente — falha em retry. "
        "Ver docs/adr/ADR-004-idempotent-service-layer-provisioning.md"
    )


def test_adr004_signal_is_thin_dispatcher():
    """ADR-004: signals.py não deve conter lógica de negócio (get_or_create, migrate_schemas)."""
    src = (BASE_DIR / "apps" / "tenants" / "signals.py").read_text()
    business_logic_patterns = ["get_or_create", "migrate_schemas", "slugify"]
    violations = [p for p in business_logic_patterns if p in src]
    assert not violations, (
        "ADR-004 VIOLADO: Lógica de negócio encontrada em signals.py: "
        + str(violations)
        + ". Mover para apps/tenants/services.py. "
        "Ver docs/adr/ADR-004-idempotent-service-layer-provisioning.md"
    )


# ---------------------------------------------------------------------------
# ADR-005: TenantAwareBackend primeiro em AUTHENTICATION_BACKENDS
# Risco se violado: login user@tenant não funciona
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_adr005_tenant_aware_backend_registered():
    """ADR-005: TenantAwareBackend deve estar em AUTHENTICATION_BACKENDS."""
    from django.conf import settings
    assert "core.auth_backends.TenantAwareBackend" in settings.AUTHENTICATION_BACKENDS, (
        "ADR-005 VIOLADO: TenantAwareBackend não registado em AUTHENTICATION_BACKENDS. "
        "Login user@tenant-domain não funciona. "
        "Ver docs/adr/ADR-005-tenant-aware-auth-backend.md"
    )


@pytest.mark.django_db
def test_adr005_tenant_aware_backend_is_first():
    """ADR-005: TenantAwareBackend deve ser o primeiro backend na cadeia."""
    from django.conf import settings
    backends = settings.AUTHENTICATION_BACKENDS
    assert backends[0] == "core.auth_backends.TenantAwareBackend", (
        f"ADR-005 VIOLADO: TenantAwareBackend não é o primeiro backend. "
        f"Primeiro encontrado: {backends[0]}. "
        "Ver docs/adr/ADR-005-tenant-aware-auth-backend.md"
    )


# ---------------------------------------------------------------------------
# ADR-006: PostgreSQL porta 5433 em docker-compose.yml
# Risco se violado: conflito com instância local, .env desincronizado
# ---------------------------------------------------------------------------

def test_adr006_postgres_port_5433_in_compose():
    """ADR-006: docker-compose.yml deve mapear PostgreSQL para porta 5433 no host."""
    compose_file = BASE_DIR.parent / "docker-compose.yml"
    if not compose_file.exists():
        pytest.skip("docker-compose.yml não encontrado — skip em CI sem Docker")

    src = compose_file.read_text()
    assert "5433" in src, (
        "ADR-006 VIOLADO: Porta 5433 não encontrada em docker-compose.yml. "
        "PostgreSQL pode estar em conflito com instância local na porta 5432. "
        "Ver docs/adr/ADR-006-postgres-port-5433-docker.md"
    )


def test_adr006_env_port_matches_compose():
    """ADR-006: DATABASE_PORT no .env deve corresponder à porta mapeada no docker-compose.yml."""
    env_file = BASE_DIR / ".env"
    compose_file = BASE_DIR.parent / "docker-compose.yml"

    if not env_file.exists() or not compose_file.exists():
        pytest.skip(".env ou docker-compose.yml não encontrado")

    env_port = None
    for line in env_file.read_text().splitlines():
        if line.startswith("DATABASE_PORT="):
            env_port = line.split("=", 1)[1].strip()
            break

    compose_src = compose_file.read_text()
    assert env_port and env_port in compose_src, (
        f"ADR-006 VIOLADO: DATABASE_PORT={env_port} no .env não encontrado em docker-compose.yml. "
        "Portas desincronizadas — Django pode não conseguir conectar. "
        "Ver docs/adr/ADR-006-postgres-port-5433-docker.md"
    )
