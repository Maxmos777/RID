"""
Auth-check endpoint for Traefik forwardAuth.

Traefik sends every inbound request here; Django answers:
  200 — user authenticated and belongs to the tenant
  401 — no active session (Traefik redirects to login)
  403 — session exists but user lacks tenant membership
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from django.db import connection
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

if TYPE_CHECKING:
    from django.http import HttpRequest

from apps.accounts.models import TenantMembership

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: validate next URL to prevent open-redirect
# ---------------------------------------------------------------------------

def is_safe_next_url(next_url: str) -> bool:
    """Return True only for absolute internal paths (starts with '/', not '//')."""
    if not isinstance(next_url, str):
        return False
    if not next_url:
        return False
    # Must start with exactly one slash — no protocol-relative, no schemes
    if not next_url.startswith("/"):
        return False
    if next_url.startswith("//"):
        return False
    if "://" in next_url:
        return False
    return True


# ---------------------------------------------------------------------------
# Async fire-and-forget audit logger
# ---------------------------------------------------------------------------

def _write_audit_event(
    tenant_schema: str,
    user_id: str,
    user_email: str,
    original_url: str,
) -> None:
    """Log auth-check event. Runs in a daemon thread so it never blocks the response."""
    logger.info(
        "auth_check tenant=%s user=%s email=%s url=%s",
        tenant_schema,
        user_id,
        user_email,
        original_url,
    )


# ---------------------------------------------------------------------------
# View: /internal/auth-check/
# ---------------------------------------------------------------------------

@csrf_exempt
@require_GET
def auth_check(request: HttpRequest) -> HttpResponse:
    """
    Traefik forwardAuth endpoint.

    Returns:
      200 — authenticated + tenant member
      401 — anonymous / no session
      403 — authenticated but not a member of current tenant
    """
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    tenant_schema = connection.schema_name
    original_url = request.META.get("HTTP_X_FORWARDED_URI", request.get_full_path())

    has_membership = TenantMembership.objects.filter(
        user=request.user,
        tenant_schema=tenant_schema,
        is_active=True,
    ).exists()

    if not has_membership:
        # Fire audit in daemon thread
        threading.Thread(
            target=_write_audit_event,
            args=(tenant_schema, str(request.user.pk), request.user.email, original_url),
            daemon=True,
        ).start()
        return HttpResponse(status=403)

    return HttpResponse(status=200)
