"""
Langflow HTTP client.

Wraps Langflow's REST API:
  POST /api/v1/login        → get superuser JWT
  POST /api/v1/users/       → create a Langflow user
  GET  /api/v1/users/whoami → verify a JWT is valid
  POST /api/v1/api_key/     → create an API key for a user

All public functions return (result, error) tuples — no exceptions
propagate out of this module. Callers check the error string.

Origem: RockItDown/src/rocklangflow — adaptado para async puro (httpx).
"""
from __future__ import annotations

from typing import Any

import httpx
from django.conf import settings


async def _get_superuser_token() -> tuple[str, str | None]:
    """
    Authenticate as the Langflow superuser and return a JWT.

    Returns (token, None) on success, ("", error_message) on failure.
    """
    async with httpx.AsyncClient(
        base_url=settings.LANGFLOW_BASE_URL, timeout=10
    ) as client:
        resp = await client.post(
            "/api/v1/login",
            data={
                "username": settings.LANGFLOW_SUPERUSER,
                "password": settings.LANGFLOW_SUPERUSER_PASSWORD,
            },
        )

    if resp.status_code != 200:
        return "", f"langflow superuser login failed: {resp.status_code} — {resp.text}"

    token: str = resp.json().get("access_token", "")
    return token, None


async def get_or_create_langflow_user(
    email: str,
    password: str,
) -> tuple[dict[str, Any], str | None]:
    """
    Ensure a Langflow user exists and return their credentials.

    Flow:
      1. Login as superuser to get admin JWT
      2. POST /api/v1/users/ to create user (ignore 400 = already exists)
      3. Login as the user to get their JWT
      4. POST /api/v1/api_key/ to get/create an API key

    Returns ({"access_token": ..., "api_key": ...}, None) on success.
    Returns ({}, error_message) on failure.
    """
    superuser_token, err = await _get_superuser_token()
    if err:
        return {}, err

    headers = {"Authorization": f"Bearer {superuser_token}"}

    async with httpx.AsyncClient(
        base_url=settings.LANGFLOW_BASE_URL, timeout=10
    ) as client:
        # Create user — 400 means already exists, which is fine
        create_resp = await client.post(
            "/api/v1/users/",
            json={"username": email, "password": password},
            headers=headers,
        )
        if create_resp.status_code not in (200, 201, 400):
            return {}, f"create user failed: {create_resp.status_code} — {create_resp.text}"

        # Login as the user to get their personal JWT
        login_resp = await client.post(
            "/api/v1/login",
            data={"username": email, "password": password},
        )
        if login_resp.status_code != 200:
            return {}, f"user login failed: {login_resp.status_code} — {login_resp.text}"

        user_token: str = login_resp.json().get("access_token", "")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Create or retrieve an API key for this user
        key_resp = await client.post(
            "/api/v1/api_key/",
            json={"name": "rid-auto"},
            headers=user_headers,
        )
        api_key = ""
        if key_resp.status_code in (200, 201):
            api_key = key_resp.json().get("api_key", "")

    return {"access_token": user_token, "api_key": api_key}, None
