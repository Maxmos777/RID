"""Tests for auth_gate helpers and URL registration."""
from __future__ import annotations

import pytest
from django.urls import resolve, reverse


# ---------------------------------------------------------------------------
# is_safe_next_url
# ---------------------------------------------------------------------------

VALID_PATHS = [
    "/flows/",
    "/flows/editor?workspace=abc",
    "/app/",
    "/",
    "/internal/auth-check/",
]

INVALID_URLS = [
    pytest.param("//evil.com", id="protocol-relative"),
    pytest.param("https://evil.com", id="absolute-https"),
    pytest.param("javascript:alert(1)", id="javascript-scheme"),
    pytest.param("ftp://evil.com", id="ftp-scheme"),
    pytest.param("relative/path", id="relative-no-slash"),
    pytest.param("", id="empty-string"),
    pytest.param("flows/", id="relative-with-slash"),
    pytest.param(" /flows/", id="leading-space"),
]


class TestIsSafeNextUrl:
    """Validates that is_safe_next_url accepts only absolute internal paths."""

    @pytest.mark.parametrize("path", VALID_PATHS)
    def test_valid_paths_accepted(self, path: str) -> None:
        from apps.accounts.auth_gate import is_safe_next_url

        assert is_safe_next_url(path) is True, f"Expected True for {path!r}"

    @pytest.mark.parametrize("url", INVALID_URLS)
    def test_invalid_urls_rejected(self, url: str) -> None:
        from apps.accounts.auth_gate import is_safe_next_url

        assert is_safe_next_url(url) is False, f"Expected False for {url!r}"


# ---------------------------------------------------------------------------
# URL registration
# ---------------------------------------------------------------------------


class TestAuthCheckUrlRegistered:
    """Ensures the auth-check URL is properly registered."""

    def test_resolve_internal_auth_check(self) -> None:
        match = resolve("/internal/auth-check/")
        assert match.url_name == "auth-check"

    def test_reverse_auth_check(self) -> None:
        url = reverse("auth-check")
        assert url == "/internal/auth-check/"
