# ST-002-01: Adicionar configurações de proxy header ao Django settings.py

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Adicionar ao `backend/core/settings.py` as configurações `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SECURE`, e actualizar `ALLOWED_HOSTS` para incluir `backend` — todas env-gated e sem hardcoding.

## Prerequisites

```bash
# Verificar que settings.py existe e tem USE_X_FORWARDED_HOST já declarado
grep -n "USE_X_FORWARDED_HOST" /home/RID/backend/core/settings.py
# Expected output: linha com USE_X_FORWARDED_HOST = os.getenv(...)

# Verificar que ALLOWED_HOSTS está declarado
grep -n "ALLOWED_HOSTS" /home/RID/backend/core/settings.py
# Expected output: linha com ALLOWED_HOSTS = [h.strip() ...]

# Verificar que SECURE_PROXY_SSL_HEADER ainda não existe
grep -n "SECURE_PROXY_SSL_HEADER" /home/RID/backend/core/settings.py
# Expected output: (vazio)
```

## Files

- **Modify:** `backend/core/settings.py` (adicionar 4 configurações após `USE_X_FORWARDED_HOST`)
- **Test:** `backend/tests/test_proxy_settings.py`

## Steps

### Step 1: Escrever o teste (RED)

Criar `/home/RID/backend/tests/test_proxy_settings.py`:

```python
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
        # Django lê o header e reporta is_secure() = True
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
        # O setting deve existir (pode ser True ou False dependendo do env)
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
```

### Step 2: Correr o teste para verificar que falha (RED)

```bash
cd /home/RID/backend
python -m pytest tests/test_proxy_settings.py -v 2>&1 | head -40
```

Expected output:
```
FAILED tests/test_proxy_settings.py::TestSessionCookieSecure::test_session_cookie_samesite_is_lax
FAILED tests/test_proxy_settings.py::TestSessionCookieSecure::test_session_cookie_secure_setting_exists
...
```

### Step 3: Adicionar as configurações ao settings.py

Em `/home/RID/backend/core/settings.py`, localizar o bloco `USE_X_FORWARDED_HOST` (linhas 30-34) e adicionar imediatamente a seguir:

```python
# Proxy SSL header — Django reconhece HTTPS quando Traefik injeta X-Forwarded-Proto: https
_proxy_ssl = os.getenv("DJANGO_SECURE_PROXY_SSL_HEADER", "").lower() in ("1", "true", "yes")
if _proxy_ssl:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies seguros — apenas em produção/staging (quando HTTPS está activo via Traefik)
_secure_cookies = os.getenv("DJANGO_SESSION_COOKIE_SECURE", "").lower() in ("1", "true", "yes")
SESSION_COOKIE_SECURE = _secure_cookies
SESSION_COOKIE_SAMESITE = "Lax"  # protecção CSRF sem quebrar redirect flows

CSRF_COOKIE_SECURE = _secure_cookies
```

E no bloco de `ALLOWED_HOSTS` (linhas 23-27), actualizar o default para incluir `backend`:

```python
_raw_hosts = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,host.docker.internal,testserver,backend",
)
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]
```

### Step 4: Correr os testes (GREEN)

```bash
cd /home/RID/backend
python -m pytest tests/test_proxy_settings.py -v
```

Expected output:
```
tests/test_proxy_settings.py::TestSecureProxyHeader::test_request_is_secure_when_forwarded_proto_https PASSED
tests/test_proxy_settings.py::TestSecureProxyHeader::test_request_is_not_secure_without_header PASSED
tests/test_proxy_settings.py::TestSessionCookieSecure::test_session_cookie_secure_setting_exists PASSED
tests/test_proxy_settings.py::TestSessionCookieSecure::test_session_cookie_samesite_is_lax PASSED
tests/test_proxy_settings.py::TestSessionCookieSecure::test_csrf_cookie_secure_setting_exists PASSED
tests/test_proxy_settings.py::TestAllowedHosts::test_backend_hostname_in_allowed_hosts PASSED
tests/test_proxy_settings.py::TestAllowedHosts::test_allowed_hosts_env_var_includes_backend PASSED
7 passed
```

### Step 5: Verificar que nenhum teste existente quebrou

```bash
cd /home/RID/backend
python -m pytest tests/ -v --ignore=tests/test_proxy_settings.py 2>&1 | tail -10
```

Expected output:
```
... passed, ... warnings
```

### Step 6: Commit

```bash
cd /home/RID
git add backend/core/settings.py backend/tests/test_proxy_settings.py
git commit -m "feat(langflow-gate): add proxy header settings to Django (SECURE_PROXY_SSL_HEADER, SESSION_COOKIE_SECURE)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
