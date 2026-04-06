"""
Tests for Django proxy settings env vars documentation in .env.example.

Validates that ST-002-02 correctly documents all proxy-related env vars.

Feature: rid-langflow-single-entry
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = REPO_ROOT / "backend" / ".env.example"


def _content() -> str:
    return ENV_EXAMPLE.read_text()


def test_django_secure_proxy_ssl_header_documented():
    """ST-002-02: DJANGO_SECURE_PROXY_SSL_HEADER must be documented."""
    assert "DJANGO_SECURE_PROXY_SSL_HEADER" in _content(), (
        "DJANGO_SECURE_PROXY_SSL_HEADER not found in .env.example. "
        "Required for Traefik HTTPS passthrough."
    )


def test_django_session_cookie_secure_documented():
    """ST-002-02: DJANGO_SESSION_COOKIE_SECURE must be documented."""
    assert "DJANGO_SESSION_COOKIE_SECURE" in _content(), (
        "DJANGO_SESSION_COOKIE_SECURE not found in .env.example."
    )


def test_django_csrf_cookie_secure_documented():
    """ST-002-02: DJANGO_CSRF_COOKIE_SECURE must be documented."""
    assert "DJANGO_CSRF_COOKIE_SECURE" in _content(), (
        "DJANGO_CSRF_COOKIE_SECURE not found in .env.example."
    )


def test_django_use_x_forwarded_host_documented():
    """ST-002-02: DJANGO_USE_X_FORWARDED_HOST must be documented."""
    assert "DJANGO_USE_X_FORWARDED_HOST" in _content(), (
        "DJANGO_USE_X_FORWARDED_HOST not found in .env.example. "
        "Required for HeaderFirstTenantMiddleware to resolve tenant from Host header."
    )


def test_django_allowed_hosts_includes_backend():
    """ST-002-02: DJANGO_ALLOWED_HOSTS example must include 'backend'."""
    content = _content()
    assert "DJANGO_ALLOWED_HOSTS" in content, (
        "DJANGO_ALLOWED_HOSTS not documented in .env.example."
    )
    # Find the line with DJANGO_ALLOWED_HOSTS and verify 'backend' is in it
    for line in content.splitlines():
        if line.startswith("DJANGO_ALLOWED_HOSTS"):
            assert "backend" in line, (
                f"'backend' not in DJANGO_ALLOWED_HOSTS example: {line!r}. "
                "Traefik forwardAuth sub-requests use 'backend' hostname."
            )
            break


def test_proxy_section_has_comment():
    """ST-002-02: .env.example must have a proxy settings section comment."""
    assert "Proxy" in _content() or "proxy" in _content(), (
        "No proxy section comment found in .env.example."
    )
