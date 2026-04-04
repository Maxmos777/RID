"""
Pré-requisitos PostgreSQL para Langflow na mesma database que o Django (ADR-009).

Fonte única de verdade para DDL idempotente (role + schema + privilégios + search_path).
Substitui a lógica duplicada em shell/SQL manual — executar via:

    python manage.py ensure_langflow_schema

Requisitos: o utilizador da `DATABASE_URL` do Django deve ter privilégios de superuser
ou equivalentes (CREATE ROLE, CREATE SCHEMA) — típico em `POSTGRES_USER` da imagem oficial.
"""
from __future__ import annotations

import logging
import os

from django.db import connection
from psycopg2 import sql as psql

logger = logging.getLogger(__name__)

LANGFLOW_PG_ROLE = "langflow"
LANGFLOW_PG_SCHEMA = "langflow"


def ensure_langflow_pg_prerequisites(*, password: str | None = None) -> None:
    """
    Idempotente: cria role `langflow`, schema `langflow`, grants e search_path no role.

    Raises:
        django.db.Error: falha de ligação ou permissões insuficientes.
        ValueError: configuração de database inválida.
    """
    pw = (
        password
        if password is not None
        else os.environ.get("LANGFLOW_DB_PASSWORD", "langflow")
    )
    conn = connection
    conn.ensure_connection()
    db_name = conn.settings_dict.get("NAME")
    if not isinstance(db_name, str) or not db_name:
        msg = "DATABASES['default']['NAME'] must be a non-empty string"
        raise ValueError(msg)

    old_autocommit = conn.get_autocommit()
    conn.set_autocommit(True)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = %s",
                [LANGFLOW_PG_ROLE],
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    psql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(
                        psql.Identifier(LANGFLOW_PG_ROLE),
                    ),
                    [pw],
                )
                logger.info("PostgreSQL role %s created", LANGFLOW_PG_ROLE)

            cursor.execute(
                psql.SQL(
                    "CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}"
                ).format(
                    psql.Identifier(LANGFLOW_PG_SCHEMA),
                    psql.Identifier(LANGFLOW_PG_ROLE),
                ),
            )

            cursor.execute(
                psql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    psql.Identifier(db_name),
                    psql.Identifier(LANGFLOW_PG_ROLE),
                ),
            )

            cursor.execute(
                psql.SQL(
                    "ALTER ROLE {} IN DATABASE {} SET search_path TO {}, public"
                ).format(
                    psql.Identifier(LANGFLOW_PG_ROLE),
                    psql.Identifier(db_name),
                    psql.Identifier(LANGFLOW_PG_SCHEMA),
                ),
            )

            cursor.execute(
                psql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(
                    psql.Identifier(LANGFLOW_PG_SCHEMA),
                ),
            )
            cursor.execute(
                psql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    psql.Identifier(LANGFLOW_PG_SCHEMA),
                    psql.Identifier(LANGFLOW_PG_ROLE),
                ),
            )

            lf_id = psql.Identifier(LANGFLOW_PG_ROLE)
            sch_id = psql.Identifier(LANGFLOW_PG_SCHEMA)
            cursor.execute(
                psql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {lf} IN SCHEMA {sch} "
                    "GRANT ALL ON TABLES TO {lf}"
                ).format(lf=lf_id, sch=sch_id),
            )
            cursor.execute(
                psql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {lf} IN SCHEMA {sch} "
                    "GRANT ALL ON SEQUENCES TO {lf}"
                ).format(lf=lf_id, sch=sch_id),
            )

        logger.info(
            "Langflow PostgreSQL prerequisites OK (schema=%s, database=%s)",
            LANGFLOW_PG_SCHEMA,
            db_name,
        )
    finally:
        conn.set_autocommit(old_autocommit)
