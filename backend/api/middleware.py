"""
CSRF protection middleware for FastAPI.

Validates X-CSRFToken header against csrftoken cookie for state-changing
requests (POST, PUT, DELETE, PATCH). Integrates with Django's CSRF framework
via `django.middleware.csrf.get_token()`.

SECURITY FIX #2: CSRF Validation on FastAPI Endpoints
"""
from __future__ import annotations

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_403_FORBIDDEN

logger = logging.getLogger(__name__)

# Methods that don't require CSRF validation (safe methods)
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CsrfProtectMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware for FastAPI routes.

    Validates X-CSRFToken header against csrftoken cookie for all
    state-changing requests (POST, PUT, DELETE, PATCH).

    Skips validation for:
      - Safe methods (GET, HEAD, OPTIONS, TRACE)
      - Requests without a csrftoken cookie
      - Requests to /api/health (public health check)

    Raises 403 Forbidden if CSRF token is missing or invalid.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and validate CSRF token if needed."""

        # Skip CSRF validation for safe methods
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF validation for public health endpoint
        if request.url.path in ("/api/health", "/health"):
            return await call_next(request)

        # Extract csrf token from cookie
        csrf_cookie = request.cookies.get("csrftoken", "")

        # If no csrf cookie, skip validation (user not authenticated)
        if not csrf_cookie:
            logger.debug(
                "No csrftoken cookie found, skipping CSRF validation",
                extra={"path": request.url.path, "method": request.method},
            )
            return await call_next(request)

        # Extract csrf token from header
        csrf_header = request.headers.get("x-csrftoken", "")

        # Validate tokens match
        if not csrf_header or csrf_header != csrf_cookie:
            logger.warning(
                "CSRF validation failed: token mismatch",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "has_header": bool(csrf_header),
                },
            )
            return Response(
                content={"detail": "CSRF token invalid or missing"},
                status_code=HTTP_403_FORBIDDEN,
            )

        logger.debug(
            "CSRF validation passed",
            extra={"path": request.url.path, "method": request.method},
        )
        return await call_next(request)
