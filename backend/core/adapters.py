"""
TenantAwareAccountAdapter: preserva dados de tenant durante o signup allauth.

Origem: RockItDown/src/core/adapters.py (adaptado).
Melhorias:
  - logging em vez de print()
  - confirm_email removido (allauth v65+ funciona correctamente sem override)

Fluxo de dados:
  Formulário de signup -> save_user() -> session["_signup_tenant_name"]
    -> email_confirmed signal -> provision_tenant_for_user()

O adapter não cria o tenant — apenas preserva os dados do formulário
para o signal ter acesso após confirmação de email.
"""
from __future__ import annotations

import logging

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class TenantAwareAccountAdapter(DefaultAccountAdapter):
    """
    Adapter allauth que persiste dados de tenant do formulário na sessão.

    Campos lidos do formulário:
      - tenant_name: nome do tenant a criar (obrigatório no signup)
    """

    def save_user(self, request, user, form, commit=True):  # type: ignore[override]
        user = super().save_user(request, user, form, commit=commit)

        if form is not None and request is not None and hasattr(request, "session"):
            tenant_name = (
                form.cleaned_data.get("tenant_name")
                or form.cleaned_data.get("username")
                or ""
            )
            request.session["_signup_tenant_name"] = tenant_name
            request.session.save()
            logger.debug(
                "Dados de tenant preservados na sessão para utilizador %s: tenant_name=%r",
                getattr(user, "email", "?"),
                tenant_name,
            )

        return user
