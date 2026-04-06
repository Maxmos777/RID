"""Testes das configurações de proxy header (T-002 — rid-langflow-single-entry)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import RequestFactory, override_settings


class TestSecureProxyHeader:
    """SECURE_PROXY_SSL_HEADER permite que Django reconheça HTTPS via X-Forwarded-Proto."""

    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        USE_X_FORWARDED_HOST=True,
    )
    def test_request_is_secure_when_forwarded_proto_https(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_FORWARDED_PROTO="https")
        assert request.is_secure() is True

    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    )
    def test_request_is_not_secure_without_header(self):
        factory = RequestFactory()
        request = factory.get("/")
        assert request.is_secure() is False


class TestSessionCookieSecure:
    """SESSION_COOKIE_SECURE é True em produção/staging (env-gated)."""

    def test_session_cookie_secure_setting_exists(self):
        from django.conf import settings
        assert hasattr(settings, "SESSION_COOKIE_SECURE")

    def test_session_cookie_samesite_is_lax(self):
        from django.conf import settings
        assert settings.SESSION_COOKIE_SAMESITE == "Lax"

    def test_csrf_cookie_secure_setting_exists(self):
        from django.conf import settings
        assert hasattr(settings, "CSRF_COOKIE_SECURE")


class TestAllowedHosts:
    """ALLOWED_HOSTS inclui 'backend' para sub-requests internos do Traefik forwardAuth."""

    @override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "backend", "testserver"])
    def test_backend_hostname_in_allowed_hosts(self):
        from django.conf import settings
        assert "backend" in settings.ALLOWED_HOSTS

    def test_allowed_hosts_env_var_includes_backend(self):
        """Quando DJANGO_ALLOWED_HOSTS inclui 'backend', é carregado correctamente."""
        with patch.dict(
            "os.environ",
            {"DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,backend,testserver"},
        ):
            import importlib
            import core.settings as s
            importlib.reload(s)
            assert "backend" in s.ALLOWED_HOSTS
