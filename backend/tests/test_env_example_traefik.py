"""
Tests for Traefik/Langflow env vars documentation in .env.example.

Validates that ST-001-03 correctly documents all required env vars.

Feature: rid-langflow-single-entry
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = REPO_ROOT / "backend" / ".env.example"


def test_env_example_exists():
    """ST-001-03: .env.example must exist."""
    assert ENV_EXAMPLE.exists(), f".env.example not found at {ENV_EXAMPLE}"


def test_langflow_base_url_documented():
    """ST-001-03: LANGFLOW_BASE_URL must be documented with internal URL."""
    content = ENV_EXAMPLE.read_text()
    assert "LANGFLOW_BASE_URL" in content, (
        "LANGFLOW_BASE_URL not found in .env.example. "
        "Required to document internal Langflow URL after port 7861 removal."
    )
    assert "langflow:7860" in content, (
        "Internal URL http://langflow:7860 not documented in .env.example."
    )


def test_langflow_cors_origins_documented():
    """ST-001-03: LANGFLOW_CORS_ORIGINS must be documented."""
    content = ENV_EXAMPLE.read_text()
    assert "LANGFLOW_CORS_ORIGINS" in content, (
        "LANGFLOW_CORS_ORIGINS not found in .env.example. "
        "Required to configure allowed CORS origins for Langflow."
    )


def test_traefik_section_has_comment():
    """ST-001-03: .env.example must have a Traefik section comment."""
    content = ENV_EXAMPLE.read_text()
    assert "Traefik" in content, (
        "Traefik section comment not found in .env.example. "
        "New sections must have explanatory comments."
    )
