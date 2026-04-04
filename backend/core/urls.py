from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.accounts.views import RockItDownSPA

urlpatterns = [
    # /           → /app/
    path("", RedirectView.as_view(url="/app/", permanent=False)),
    # /app/       → RockItDown SPA (LoginRequired)
    path("app/", RockItDownSPA.as_view(), name="rockitdown-spa"),

    # django-allauth
    path("accounts/", include("allauth.urls")),

    # Django admin
    path("admin/", admin.site.urls),
]
