from __future__ import annotations

import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token
from django.views.generic import TemplateView


class RockItDownSPA(LoginRequiredMixin, TemplateView):
    """
    Entry point do SPA (servido por Django templates).

    - Enforce login via LoginRequiredMixin
    - Renderiza HTML com bundle do React
    - Injeta contexto server-side (tenant + endpoints + csrf) em JSON
      para o React bootstrap sem round-trip extra.
    """

    template_name = "apps/rockitdown/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        request = self.request

        # Tenant schema resolvido pelo TenantMainMiddleware (para requests Django).
        from django.db import connection

        schema_name = getattr(connection, "schema_name", "public")

        tenant_info: dict[str, str] = {
            "schema_name": str(schema_name),
            "user_email": str(request.user.email),
            "user_id": str(request.user.pk),
        }

        api_config: dict[str, str] = {
            "base_url": "/api/v1",
            "langflow_auto_login_url": "/api/v1/langflow/auth/auto-login",
            "langflow_base_url": str(settings.LANGFLOW_BASE_URL),
        }

        ctx["app_config_json"] = json.dumps(
            {
                "tenant": tenant_info,
                "api": api_config,
                "csrf_token": get_token(request),
            }
        )
        return ctx

