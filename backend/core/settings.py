"""
Django settings for RID platform.

Multi-tenant via django-tenants (schema-per-tenant).
FastAPI mounted at /api/* via ASGI.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# Host header permitido (vírgulas). testserver = Django test Client por defeito.
_raw_hosts = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,host.docker.internal,testserver,backend",
)
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]

# Reverso-proxy que define X-Forwarded-Host (opcional)
USE_X_FORWARDED_HOST = os.getenv("DJANGO_USE_X_FORWARDED_HOST", "").lower() in (
    "1",
    "true",
    "yes",
)

# Proxy SSL header — Django reconhece HTTPS quando Traefik injeta X-Forwarded-Proto: https
_proxy_ssl = os.getenv("DJANGO_SECURE_PROXY_SSL_HEADER", "").lower() in ("1", "true", "yes")
if _proxy_ssl:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies seguros — apenas em produção/staging (quando HTTPS está activo via Traefik)
_secure_cookies = os.getenv("DJANGO_SESSION_COOKIE_SECURE", "").lower() in ("1", "true", "yes")
SESSION_COOKIE_SECURE = _secure_cookies
SESSION_COOKIE_SAMESITE = "Lax"  # protecção CSRF sem quebrar redirect flows
CSRF_COOKIE_SECURE = _secure_cookies

# ---------------------------------------------------------------------------
# django-tenants: MUST be first in INSTALLED_APPS
# ---------------------------------------------------------------------------
SHARED_APPS = [
    "django_tenants",
    "apps.tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "apps.accounts",
]

TENANT_APPS = [
    # Intentionally contains only contenttypes.
    # All user/auth models are shared (public schema) via SHARED_APPS.
    # Add tenant-scoped app models here as the platform grows
    # (e.g. "apps.flows", "apps.billing_usage").
    "django.contrib.contenttypes",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "tenants.Customer"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ---------------------------------------------------------------------------
# Tenant por cabeçalho (X-Tenant-Id → HTTP_X_TENANT_ID). Vazio = só hostname.
# ---------------------------------------------------------------------------
_tenant_hdr = os.getenv("TENANT_RESOLUTION_HEADER", "HTTP_X_TENANT_ID").strip()
TENANT_RESOLUTION_HEADER = _tenant_hdr or None

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.tenant_middleware.HeaderFirstTenantMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "core.urls"

# django-tenants: hostname sem entrada em tenants_domain → schema public (evita 404
# em localhost / Docker sem Domain). PUBLIC_SCHEMA_URLCONF é obrigatório para esse ramo.
# Em produção com DEBUG=False, não definir DJANGO_SHOW_PUBLIC_IF_NO_TENANT (risco de
# expor URLconf público para hosts não mapeados).
PUBLIC_SCHEMA_URLCONF = ROOT_URLCONF
_tenant_public_fallback = DEBUG or os.getenv(
    "DJANGO_SHOW_PUBLIC_IF_NO_TENANT", ""
).lower() in ("1", "true", "yes")
if _tenant_public_fallback:
    SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

# CSRF: origens adicionais (ex.: http://localhost:8000 se o proxy altera o host)
_csrf_trusted = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(",") if o.strip()]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "core.asgi.application"
WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------------------------------
# Database — django-tenants requires django.db.backends.postgresql
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.getenv("DATABASE_NAME", "rid"),
        "USER": os.getenv("DATABASE_USER", "rid"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "rid"),
        "HOST": os.getenv("DATABASE_HOST", "localhost"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
    }
}

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# ---------------------------------------------------------------------------
# Cache — Redis
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    }
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "core.auth_backends.TenantAwareBackend",  # user@tenant-domain (não é e-mail público)
    # allauth antes do ModelBackend: login por e-mail (ACCOUNT_LOGIN_METHODS) não usa USERNAME_FIELD.
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "accounts.TenantUser"

# LoginRequiredMixin (ex.: /app/) e fluxo allauth
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/"

# allauth v65+ settings
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "core.adapters.TenantAwareAccountAdapter"

# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Internationalisation (pt-BR — datas, admin e gettext por defeito)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@localhost")

# ---------------------------------------------------------------------------
# Langflow
# ---------------------------------------------------------------------------
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://localhost:7861")
LANGFLOW_SUPERUSER = os.getenv("LANGFLOW_SUPERUSER") or "admin"
LANGFLOW_SUPERUSER_PASSWORD = os.environ.get("LANGFLOW_SUPERUSER_PASSWORD")
if not LANGFLOW_SUPERUSER_PASSWORD and not DEBUG:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("LANGFLOW_SUPERUSER_PASSWORD must be set in production")
# API Key do superuser Langflow — gerada em Settings → API Keys.
# Ausente → langflow_workspace_id fica null (graceful degradation; tenant cria-se na mesma).
LANGFLOW_SUPERUSER_API_KEY: str | None = os.getenv("LANGFLOW_SUPERUSER_API_KEY") or None

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if not DEBUG and not STRIPE_SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("STRIPE_SECRET_KEY must be set in production")
