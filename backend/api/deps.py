"""
FastAPI dependencies for tenant resolution.

Django's TenantMainMiddleware does NOT run for /api/* requests.
Use get_current_tenant() as a FastAPI dependency on any route
that needs to access tenant-scoped ORM data.

Isolation strategy
------------------
Django's connection object is thread-local; it is NOT safe to call
set_tenant() from an async coroutine where multiple coroutines may
interleave between awaits on the same OS thread.

We use sync_to_async to execute ALL connection-mutating and ORM code
inside a dedicated thread-pool thread — the same isolation that
Django's TenantMainMiddleware relies on.
"""
from __future__ import annotations

from typing import Annotated

from asgiref.sync import sync_to_async
from fastapi import Depends, Header, HTTPException, Request, status


def _resolve_tenant(hostname: str) -> str:
    """
    Synchronous helper: resolves hostname -> schema and sets the tenant
    on the current DB connection.

    Must run inside sync_to_async so that it executes in an isolated
    thread-pool thread (thread-local connection safety).
    """
    from apps.tenants.models import Domain
    from django.db import connection

    try:
        domain = Domain.objects.select_related("tenant").get(domain=hostname)
    except Domain.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found for domain: {hostname}",
        )

    tenant = domain.tenant
    connection.set_tenant(tenant)
    return tenant.schema_name


async def get_current_tenant(host: Annotated[str, Header()] = "") -> str:
    """
    Resolve the current tenant from the Host header.

    Sets Django's db connection to the correct schema so ORM
    queries within the same request context hit the right schema.

    Returns the schema_name of the resolved tenant.
    Raises HTTP 400 if the Host header is missing or empty.
    Raises HTTP 404 if the domain is not registered.
    """
    hostname = host.split(":")[0].strip()

    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host header is required",
        )

    return await sync_to_async(_resolve_tenant, thread_sensitive=True)(hostname)


TenantSchema = Annotated[str, Depends(get_current_tenant)]


# ---------------------------------------------------------------------------
# Django session auth dependency
# ---------------------------------------------------------------------------

async def get_django_user(request: Request):
    """
    Extrai o utilizador Django autenticado do cookie de sessão.

    O SessionMiddleware do Django NÃO corre para requests FastAPI, por isso
    descodificamos a sessão manualmente usando o engine de sessões do Django.
    Retorna o TenantUser autenticado ou levanta 401.
    """
    from django.conf import settings as django_settings

    def _resolve_user(session_key: str):
        import django.contrib.sessions.backends.db as session_backend
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        try:
            session = session_backend.SessionStore(session_key)
            user_id = session.get("_auth_user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

    session_key = request.cookies.get(django_settings.SESSION_COOKIE_NAME)
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return await sync_to_async(_resolve_user, thread_sensitive=True)(session_key)


AuthenticatedUser = Annotated[object, Depends(get_django_user)]
