"""Fixtures for E2E Auth Gate tests — rid-langflow-single-entry."""
from __future__ import annotations
import os, subprocess, time, uuid
import pytest

COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
TRAEFIK_BASE = "http://localhost"
BACKEND_BASE = "http://localhost:8000"

@pytest.fixture(scope="session")
def compose_stack():
    if os.environ.get("SKIP_DOCKER_COMPOSE") == "1":
        pytest.skip("SKIP_DOCKER_COMPOSE=1")
        return
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "up", "-d", "--wait"],
        check=True, timeout=120,
    )
    time.sleep(3)
    yield
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "down"],
        check=False, timeout=60,
    )

@pytest.fixture
def authenticated_session(compose_stack):
    import requests
    schema = f"t_{uuid.uuid4().hex[:8]}"
    email = f"e2e-{uuid.uuid4().hex[:8]}@rid-test.local"
    password = "e2e-pw-secure-123"
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow",
         "exec", "backend", "python", "manage.py", "create_dev_user",
         "--email", email, "--password", password, "--tenant-schema", schema],
        check=True, capture_output=True, timeout=30,
    )
    session = requests.Session()
    csrf_resp = session.get(f"{BACKEND_BASE}/accounts/login/")
    csrf_token = csrf_resp.cookies.get("csrftoken", "")
    login_resp = session.post(
        f"{BACKEND_BASE}/accounts/login/",
        data={"login": email, "password": password, "csrfmiddlewaretoken": csrf_token},
        headers={"X-CSRFToken": csrf_token, "Referer": BACKEND_BASE},
        allow_redirects=True,
    )
    assert login_resp.status_code == 200
    return {"session": session, "schema": schema, "email": email}
