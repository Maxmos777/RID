"""Garante que /app/ responde com Host localhost sem Domain (Docker/browser)."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.mark.django_db
def test_app_spa_redirects_anonymous_to_login() -> None:
    """Sem sessão, /app/ redirecciona para o login (LoginRequiredMixin)."""
    client = Client()
    response = client.get("/app/", HTTP_HOST="localhost")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/accounts/login/")


@pytest.mark.django_db
def test_app_spa_200_on_localhost_without_domain() -> None:
    User = get_user_model()
    user = User.objects.create_user(
        username="spauser",
        email="spauser@example.com",
        password="test-pass-123",
    )
    client = Client()
    client.force_login(user)
    response = client.get("/app/", HTTP_HOST="localhost")
    assert response.status_code == 200
    assert b"app-config" in response.content
