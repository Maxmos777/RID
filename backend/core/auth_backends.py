"""
TenantAwareBackend: autenticação no formato user@tenant-domain ou user@schema.

Fluxo:
  1. Tenta resolver o domínio após '@' como hostname de Domain
  2. Se não encontrar, tenta como schema_name de Customer
  3. Se nenhum tenant encontrado, retorna None (outros backends tentam)
  4. Autentica o utilizador no schema público (TenantUser está em SHARED_APPS)

Diferença vs RockItDown: utilizadores estão no schema público, não no
schema do tenant — por isso não usamos schema_context para a query de auth.
"""
from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class TenantAwareBackend(ModelBackend):
    """
    Autentica utilizadores no formato 'username@tenant-domain'.

    Permite login como:
      - 'alice@acme.rid.example.com'  (hostname registado em Domain)
      - 'alice@acme'                  (schema_name do Customer)

    Se o tenant não for encontrado, delega para outros backends
    (e.g., allauth EmailBackend para login padrão por email).
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs,
    ):
        identifier = (username or email or kwargs.get("login") or "").strip()
        if not identifier or not password or "@" not in identifier:
            return None

        username_part, domain_part = identifier.split("@", 1)
        username_part = username_part.strip()
        domain_part = domain_part.strip().lower()

        if not username_part or not domain_part:
            return None

        # Verificar que o tenant existe (validação, não para trocar schema)
        tenant_exists = False
        try:
            from apps.tenants.models import Domain
            Domain.objects.select_related("tenant").get(
                Q(domain__iexact=domain_part)
            )
            tenant_exists = True
        except Domain.DoesNotExist:
            try:
                from apps.tenants.models import Customer
                Customer.objects.get(schema_name__iexact=domain_part)
                tenant_exists = True
            except Customer.DoesNotExist:
                return None

        if not tenant_exists:
            return None

        # Utilizadores no schema público — auth directa sem schema_context
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(username_part)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
