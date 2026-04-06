from __future__ import annotations

import json
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.utils import ProgrammingError
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

        # Tenant schema resolvido pelo HeaderFirstTenantMiddleware (hostname e/ou X-Tenant-Id).
        from django.db import connection
        from django_tenants.utils import get_public_schema_name

        from apps.tenants.models import Customer

        schema_name = getattr(connection, "schema_name", "public")

        public_tenant_id = ""
        if schema_name != get_public_schema_name():
            try:
                row = (
                    Customer.objects.filter(schema_name=schema_name)
                    .values_list("public_tenant_id", flat=True)
                    .first()
                )
                if row is not None:
                    public_tenant_id = str(row)
            except ProgrammingError:
                # Tabela tenants_customer sem colunas esperadas (migrações em atraso na BD).
                public_tenant_id = ""

        tenant_info: dict[str, str] = {
            "schema_name": str(schema_name),
            "public_tenant_id": public_tenant_id,
            "user_email": str(request.user.email),
            "user_id": str(request.user.pk),
        }

        api_config: dict[str, str] = {
            "base_url": "/api/v1",
            "langflow_auto_login_url": "/api/v1/langflow/auth/auto-login",
            "langflow_base_url": str(settings.LANGFLOW_BASE_URL),
        }

        # Texto e metadados só do servidor: o React só exibe o que o Django injeta no HTML.
        gerado_em = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ui_copy: dict[str, str] = {
            "idioma_conteudo": "pt-BR",
            "titulo_painel": "Painel RockItDown",
            "mensagem_servidor": (
                "Este bloco veio do Django na renderização de /app/: o servidor controla "
                "o texto exibido aqui (sem depender de chamada extra à API)."
            ),
            "gerado_em": gerado_em,
        }

        ctx["app_config_json"] = json.dumps(
            {
                "tenant": tenant_info,
                "api": api_config,
                "csrf_token": get_token(request),
                "ui": ui_copy,
            }
        )
        return ctx
