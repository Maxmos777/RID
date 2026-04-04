"""Tests for Langflow PostgreSQL bootstrap (idempotent DDL)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from apps.tenants.langflow_pg_bootstrap import (
    LANGFLOW_PG_ROLE,
    LANGFLOW_PG_SCHEMA,
    ensure_langflow_pg_prerequisites,
)


@pytest.mark.django_db
@patch("apps.tenants.langflow_pg_bootstrap.connection")
def test_ensure_langflow_pg_prerequisites_creates_role_when_missing(mock_conn: MagicMock) -> None:
    cursor = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = cursor
    ctx.__exit__.return_value = None
    mock_conn.cursor.return_value = ctx
    mock_conn.get_autocommit.return_value = False
    mock_conn.settings_dict = {"NAME": "rid"}
    cursor.fetchone.return_value = None

    ensure_langflow_pg_prerequisites(password="test-secret")

    mock_conn.ensure_connection.assert_called_once()
    mock_conn.set_autocommit.assert_called()
    assert cursor.execute.call_count >= 6
    mock_conn.set_autocommit.assert_called_with(False)


@pytest.mark.django_db
@patch("apps.tenants.langflow_pg_bootstrap.connection")
def test_ensure_langflow_pg_prerequisites_skips_create_when_role_exists(
    mock_conn: MagicMock,
) -> None:
    cursor = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = cursor
    ctx.__exit__.return_value = None
    mock_conn.cursor.return_value = ctx
    mock_conn.get_autocommit.return_value = False
    mock_conn.settings_dict = {"NAME": "rid"}
    cursor.fetchone.return_value = (1,)

    ensure_langflow_pg_prerequisites(password="x")

    rendered = [str(c.args[0]) for c in cursor.execute.call_args_list if c.args]
    assert not any("CREATE ROLE" in f for f in rendered)


def test_constants_match_adr() -> None:
    assert LANGFLOW_PG_ROLE == "langflow"
    assert LANGFLOW_PG_SCHEMA == "langflow"
