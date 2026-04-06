"""Tests for the flows error page — ST-004-01."""
from __future__ import annotations

import time

import pytest
from django.test import Client as DjangoClient
from django.urls import reverse


@pytest.fixture
def http_client():
    """Django test client (avoids clash with conftest async client)."""
    return DjangoClient()


@pytest.mark.django_db
class TestFlowsErrorPageView:
    """HTTP-level behaviour of GET /flows/error/."""

    def test_returns_200(self, http_client):
        response = http_client.get("/flows/error/")
        assert response.status_code == 200

    def test_returns_html_content_type(self, http_client):
        response = http_client.get("/flows/error/")
        assert "text/html" in response["Content-Type"]

    def test_url_name_resolves(self):
        url = reverse("flows-error")
        assert url == "/flows/error/"

    def test_response_under_200ms(self, http_client):
        start = time.monotonic()
        http_client.get("/flows/error/")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 200, f"Response took {elapsed_ms:.0f}ms (limit 200ms)"


@pytest.mark.django_db
class TestFlowsErrorPageContent:
    """Template content checks for accessibility and branding."""

    @pytest.fixture(autouse=True)
    def _fetch_page(self, http_client):
        self.response = http_client.get("/flows/error/")
        self.content = self.response.content.decode("utf-8")

    def test_contains_retry_cta(self):
        assert "Tentar novamente" in self.content

    def test_contains_back_cta(self):
        assert "Voltar ao painel" in self.content

    def test_no_langflow_port_references(self):
        for port in ("7860", "7861"):
            assert port not in self.content, f"Found Langflow port {port} in page"
        assert "langflow" not in self.content.lower(), "Found 'langflow' reference"

    def test_has_role_main(self):
        assert 'role="main"' in self.content

    def test_has_lang_pt_br(self):
        assert 'lang="pt-BR"' in self.content

    def test_has_aria_labels(self):
        assert 'aria-label=' in self.content
