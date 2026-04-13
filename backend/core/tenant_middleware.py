"""
Resolução de tenant por cabeçalho UUID antes do hostname (django-tenants stock).

Substitui o papel de pacotes como django-tenants-url (incompatíveis com Django 6),
usando `Customer.public_tenant_id` e a chave WSGI em `TENANT_RESOLUTION_HEADER`
(por defeito `HTTP_X_TENANT_ID`, ou seja, cabeçalho HTTP `X-Tenant-Id`).

Segurança: em produção, só proxies de confiança devem poder injectar esse cabeçalho;
remova-o de pedidos vindos directamente de clientes não confiáveis se não for
necessário, ou defina `TENANT_RESOLUTION_HEADER` vazio para desactivar o ramo.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.db.utils import ProgrammingError
from django.http import HttpResponseNotFound
from django_tenants.middleware.main import TenantMainMiddleware

from apps.tenants.models import Customer


class HeaderFirstTenantMiddleware(TenantMainMiddleware):
    def get_tenant(self, domain_model, hostname):
        """
        O stock faz ``select_related('tenant')`` e carrega todas as colunas de Customer.
        Se a tabela ``tenants_customer`` estiver desalinhada do modelo (ex.: ``0001`` em
        ``--fake`` sem criar ``langflow_workspace_id``), isso gera ProgrammingError.
        ``connection.set_tenant()`` só precisa de ``schema_name`` no instance.
        """
        try:
            return super().get_tenant(domain_model, hostname)
        except ProgrammingError:
            tenant_pk = (
                domain_model.objects.filter(domain=hostname)
                .values_list("tenant_id", flat=True)
                .first()
            )
            if tenant_pk is None:
                raise domain_model.DoesNotExist from None
            try:
                return Customer.objects.only("id", "schema_name").get(pk=tenant_pk)
            except Customer.DoesNotExist:
                raise domain_model.DoesNotExist from None

    def process_request(self, request):
        connection.set_schema_to_public()

        meta_key = getattr(settings, "TENANT_RESOLUTION_HEADER", None)
        if meta_key:
            raw = (request.META.get(meta_key) or "").strip()
            if raw:
                tenant = self._tenant_from_public_id(raw)
                if tenant is not None:
                    try:
                        hostname = self.hostname_from_request(request)
                    except DisallowedHost:
                        return HttpResponseNotFound()
                    tenant.domain_url = hostname
                    request.tenant = tenant
                    connection.set_tenant(tenant)
                    self.setup_url_routing(request)
                    return None

        return super().process_request(request)

    @staticmethod
    def _tenant_from_public_id(raw: str) -> Customer | None:
        try:
            uid = uuid.UUID(raw)
        except ValueError:
            return None
        try:
            return (
                Customer.objects.filter(public_tenant_id=uid)
                .only("id", "schema_name")
                .first()
            )
        except ProgrammingError:
            # Coluna public_tenant_id (ou tabela) inexistente — ignorar cabeçalho.
            return None
