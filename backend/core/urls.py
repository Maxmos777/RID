from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.auth_gate import auth_check
from apps.accounts.views import RockItDownSPA, flows_error

urlpatterns = [
    # Traefik forwardAuth — no CSRF, no login required
    path("internal/auth-check/", auth_check, name="auth-check"),

    # /           → /app/
    path("", RedirectView.as_view(url="/app/", permanent=False)),
    # /app/       → RockItDown SPA (LoginRequired)
    path("app/", RockItDownSPA.as_view(), name="rockitdown-spa"),

    # Flows error fallback (no login required — shown by Traefik on upstream failure)
    path("flows/error/", flows_error, name="flows-error"),

    # django-allauth
    path("accounts/", include("allauth.urls")),

    # Django admin
    path("admin/", admin.site.urls),
]
