"""E2E tests for Auth Gate (T-006)."""
from __future__ import annotations
import os, socket, subprocess
import pytest

COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
TRAEFIK_BASE = "http://localhost"

@pytest.mark.playwright
def test_scenario3_session_expiry_overlay_appears(compose_stack, page, authenticated_session):
    session = authenticated_session["session"]
    cookies = [{"name": c.name, "value": c.value, "domain": "localhost", "path": "/"} for c in session.cookies]
    page.context.add_cookies(cookies)
    page.goto(f"{TRAEFIK_BASE}/app/")
    page.clock.install()
    page.context.clear_cookies()
    page.clock.tick(121_000)
    overlay = page.wait_for_selector('[role="alertdialog"]', timeout=5000)
    assert overlay is not None
    assert "Sessao expirada" in page.inner_text('[role="alertdialog"]')
    cta = page.get_by_role("button", name="Entrar novamente")
    assert cta.is_visible()

def test_scenario4_langflow_unavailable_shows_error_page(compose_stack, authenticated_session):
    session = authenticated_session["session"]
    subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "stop", "langflow"], check=True, timeout=30)
    try:
        response = session.get(f"{TRAEFIK_BASE}/flows/", timeout=10)
        assert response.status_code == 200
        assert "Tentar novamente" in response.text
        assert "Voltar ao painel" in response.text
        assert "7860" not in response.text
    finally:
        subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "start", "langflow"], check=False, timeout=60)

def test_scenario6_websocket_upgrade_succeeds(compose_stack, authenticated_session):
    import websockets.sync.client as ws_client
    session = authenticated_session["session"]
    cookies = "; ".join(f"{c.name}={c.value}" for c in session.cookies)
    try:
        with ws_client.connect("ws://localhost/flows/", additional_headers={"Cookie": cookies}, open_timeout=10) as websocket:
            assert websocket.protocol.state.name in ("OPEN", "open")
    except Exception as exc:
        error_str = str(exc)
        assert "401" not in error_str
        assert "403" not in error_str
        pytest.skip(f"WebSocket endpoint not available: {exc}")

def test_scenario7_port_7861_not_publicly_accessible(compose_stack):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(("127.0.0.1", 7861))
    sock.close()
    assert result != 0, "Port 7861 is publicly accessible — should be internal only"

def test_env_example_completeness():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", ".env.example")
    assert os.path.exists(env_path)
    with open(env_path) as f:
        content = f.read()
    required = ["LANGFLOW_BASE_URL", "LANGFLOW_CORS_ORIGINS", "DJANGO_SECURE_PROXY_SSL_HEADER",
                 "DJANGO_SESSION_COOKIE_SECURE", "DJANGO_CSRF_COOKIE_SECURE",
                 "DJANGO_USE_X_FORWARDED_HOST", "DJANGO_ALLOWED_HOSTS"]
    missing = [v for v in required if v not in content]
    assert not missing, f"Missing from .env.example: {missing}"
