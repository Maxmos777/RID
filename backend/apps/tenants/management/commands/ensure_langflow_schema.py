"""Management command: idempotent PostgreSQL role/schema for Langflow (ADR-009)."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.tenants.langflow_pg_bootstrap import ensure_langflow_pg_prerequisites


class Command(BaseCommand):
    help = (
        "Garante role e schema PostgreSQL para Langflow na mesma database que o Django "
        "(idempotente). Variável LANGFLOW_DB_PASSWORD define a password do role."
    )

    def handle(self, *args, **options) -> None:
        ensure_langflow_pg_prerequisites()
        self.stdout.write(self.style.SUCCESS("ensure_langflow_schema: OK"))
