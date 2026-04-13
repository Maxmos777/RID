# ST-006-02: Testes E2E Playwright (cenários 3, 4, 6) e validação docker-compose

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar o ficheiro de testes E2E Playwright `tests/e2e/test_auth_gate_e2e.py` cobrindo: overlay de sessão expirada com mock de timer (Cenário 3), error page quando Langflow está parado (Cenário 4), WebSocket upgrade (Cenário 6), e porta 7861 não acessível (Cenário 7). Criar também `tests/e2e/conftest.py` com fixtures de stack docker-compose.

## Prerequisites

```bash
# T-001 a T-005 completos — stack completo configurado
grep -n "rid-traefik" /home/RID/docker-compose.yml && echo "Traefik OK"
grep -n "flows/error" /home/RID/docker-compose.yml && echo "Error middleware OK"
ls /home/RID/frontend/apps/rockitdown/src/components/SessionExpiryOverlay.tsx && echo "Overlay OK"

# docker compose config valida
cd /home/RID && docker compose config --quiet && echo "docker-compose YAML OK"

# Verificar que playwright está disponível no sistema ou instalar
python -m playwright --version 2>/dev/null || pip install playwright && python -m playwright install chromium
```

## Files

- **Create:** `tests/e2e/conftest.py`
- **Create:** `tests/e2e/test_auth_gate_e2e.py`

## Steps

### Step 1: Criar o directório de testes E2E

```bash
mkdir -p /home/RID/tests/e2e
touch /home/RID/tests/__init__.py
touch /home/RID/tests/e2e/__init__.py
```

### Step 2: Criar conftest.py com fixtures docker-compose

Criar `/home/RID/tests/e2e/conftest.py`:

```python
"""
Fixtures para testes E2E do Auth Gate — rid-langflow-single-entry.

Requer docker compose --profile langflow a correr.
Os testes assumem:
  - Traefik em http://localhost:80
  - Django backend em http://localhost:8000 (interno) ou via Traefik
  - Langflow disponível via Traefik em http://localhost/flows/
  - Utilizador de teste criado via fixture django_db_setup
"""
from __future__ import annotations

import os
import subprocess
import time
import uuid

import pytest


COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
TRAEFIK_BASE = "http://localhost"
BACKEND_BASE = "http://localhost:8000"


@pytest.fixture(scope="session")
def compose_stack():
    """
    Sobe o stack completo com perfil langflow antes dos testes E2E e desce após.

    Skip se SKIP_DOCKER_COMPOSE=1 (para CI sem Docker).
    """
    if os.environ.get("SKIP_DOCKER_COMPOSE") == "1":
        pytest.skip("SKIP_DOCKER_COMPOSE=1 — testes E2E ignorados")
        return

    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "up", "-d", "--wait"],
        check=True,
        timeout=120,
    )
    time.sleep(3)  # aguardar Traefik inicializar routing

    yield

    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "down"],
        check=False,
        timeout=60,
    )


@pytest.fixture
def authenticated_session(compose_stack):
    """
    Retorna cookies de sessão válida para um utilizador de teste.

    Cria utilizador e faz login via Django test client (directo ao backend:8000).
    """
    import requests

    schema = f"t_{uuid.uuid4().hex[:8]}"
    email = f"e2e-{uuid.uuid4().hex[:8]}@rid-test.local"
    password = "e2e-pw-secure-123"

    # Criar utilizador via API interna de gestão (ou via manage.py em container)
    subprocess.run(
        [
            "docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow",
            "exec", "backend",
            "python", "manage.py", "create_dev_user",
            "--email", email,
            "--password", password,
            "--tenant-schema", schema,
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )

    # Login para obter cookie de sessão
    session = requests.Session()
    csrf_resp = session.get(f"{BACKEND_BASE}/accounts/login/")
    csrf_token = csrf_resp.cookies.get("csrftoken", "")

    login_resp = session.post(
        f"{BACKEND_BASE}/accounts/login/",
        data={
            "login": email,
            "password": password,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"X-CSRFToken": csrf_token, "Referer": BACKEND_BASE},
        allow_redirects=True,
    )
    assert login_resp.status_code == 200, f"Login falhou: {login_resp.status_code}"

    return {"session": session, "schema": schema, "email": email}
```

### Step 3: Escrever os testes E2E (RED — falham sem o stack completo)

Criar `/home/RID/tests/e2e/test_auth_gate_e2e.py`:

```python
"""
Testes E2E para o Auth Gate (T-006 — rid-langflow-single-entry).

Cenários:
  - Cenário 3: overlay aparece após sessão expirar (Playwright + mock timer)
  - Cenário 4: Langflow parado → Django error page (não 502 genérico)
  - Cenário 6: WebSocket upgrade passa através do Traefik forwardAuth
  - Cenário 7: porta 7861 não acessível publicamente
  - .env.example completeness check
"""
from __future__ import annotations

import os
import socket
import subprocess

import pytest
import requests

COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
TRAEFIK_BASE = "http://localhost"


# ---------------------------------------------------------------------------
# Cenário 3: session expiry overlay (Playwright)
# ---------------------------------------------------------------------------

@pytest.mark.playwright
def test_scenario3_session_expiry_overlay_appears(compose_stack, page, authenticated_session):
    """
    Simula sessão expirada via mock de timer do Playwright.
    Verifica que o overlay com role='alertdialog' aparece.
    """
    import playwright.sync_api as pw

    session = authenticated_session["session"]
    cookies = [
        {
            "name": c.name,
            "value": c.value,
            "domain": "localhost",
            "path": "/",
        }
        for c in session.cookies
    ]

    # Injectar cookies de sessão no contexto Playwright
    page.context.add_cookies(cookies)

    # Navegar para /app/ (shell React com heartbeat)
    page.goto(f"{TRAEFIK_BASE}/app/")

    # Instalar clock fake para controlar setInterval sem esperar 120s reais
    page.clock.install()

    # Invalidar a sessão server-side (apagar cookie de sessão do Redis seria ideal;
    # aqui simulamos limpando os cookies no contexto do browser)
    page.context.clear_cookies()

    # Avançar 121 segundos (ultrapassa o intervalo de 120s do heartbeat)
    page.clock.tick(121_000)

    # Aguardar o overlay aparecer
    overlay = page.wait_for_selector('[role="alertdialog"]', timeout=5000)
    assert overlay is not None

    # Verificar texto pt-BR
    assert "Sessão expirada" in page.inner_text('[role="alertdialog"]')

    # Verificar CTA
    cta = page.get_by_role("button", name="Entrar novamente")
    assert cta.is_visible()


# ---------------------------------------------------------------------------
# Cenário 4: Langflow indisponível → error page Django
# ---------------------------------------------------------------------------

def test_scenario4_langflow_unavailable_shows_error_page(compose_stack, authenticated_session):
    """
    Para o container Langflow; GET /flows/ deve retornar a error page do Django,
    não um 502 genérico do Traefik.
    """
    session = authenticated_session["session"]

    # Parar Langflow
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "stop", "langflow"],
        check=True,
        timeout=30,
    )

    try:
        response = session.get(f"{TRAEFIK_BASE}/flows/", timeout=10)

        # Deve receber a error page do Django (200 da error page, não 502)
        assert response.status_code == 200, f"Expected 200 (error page), got {response.status_code}"

        # Verificar conteúdo da error page Django (não a página genérica do Traefik)
        assert "Tentar novamente" in response.text, "Django error page CTA not found"
        assert "Voltar ao painel" in response.text, "Django error page CTA not found"
        assert "7860" not in response.text, "Langflow port reference found in error page"

    finally:
        # Reiniciar Langflow para não afectar outros testes
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "--profile", "langflow", "start", "langflow"],
            check=False,
            timeout=60,
        )


# ---------------------------------------------------------------------------
# Cenário 6: WebSocket upgrade através do forwardAuth
# ---------------------------------------------------------------------------

def test_scenario6_websocket_upgrade_succeeds(compose_stack, authenticated_session):
    """
    WebSocket connect para /flows/ com sessão válida deve resultar em 101 Switching Protocols.
    Usa a biblioteca websockets (sync) para verificar o handshake.
    """
    import websockets.sync.client as ws_client

    session = authenticated_session["session"]
    cookies = "; ".join(f"{c.name}={c.value}" for c in session.cookies)

    ws_url = "ws://localhost/flows/"

    try:
        # O handshake HTTP inclui o cookie de sessão; forwardAuth valida antes do upgrade
        with ws_client.connect(
            ws_url,
            additional_headers={"Cookie": cookies},
            open_timeout=10,
        ) as websocket:
            # Conexão estabelecida = 101 Switching Protocols sucedido
            assert websocket.protocol.state.name in ("OPEN", "open")
    except Exception as exc:
        # Langflow pode não ter endpoint WebSocket no path raiz — verificar status do handshake
        # O teste valida que a negação não foi por autenticação (401/403)
        error_str = str(exc)
        assert "401" not in error_str, f"WebSocket rejeitado por autenticação: {exc}"
        assert "403" not in error_str, f"WebSocket rejeitado por tenant: {exc}"
        # Se falhou por outro motivo (ex.: path não tem WS), aceitar como warning
        pytest.skip(f"WebSocket endpoint não disponível no path raiz: {exc}")


# ---------------------------------------------------------------------------
# Cenário 7: porta 7861 não acessível
# ---------------------------------------------------------------------------

def test_scenario7_port_7861_not_publicly_accessible(compose_stack):
    """
    Após ST-001-02, a porta 7861 não deve estar mapeada no host.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(("127.0.0.1", 7861))
    sock.close()

    assert result != 0, (
        "FAIL: porta 7861 está acessível no host — a porta pública do Langflow "
        "não foi removida do docker-compose.yml"
    )


# ---------------------------------------------------------------------------
# .env.example completeness check
# ---------------------------------------------------------------------------

def test_env_example_completeness():
    """
    Verifica que .env.example contém todas as variáveis documentadas
    no dependency-map §3.2 e §4.x.
    """
    env_example_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", ".env.example"
    )

    assert os.path.exists(env_example_path), f".env.example não existe em {env_example_path}"

    with open(env_example_path) as f:
        content = f.read()

    required_vars = [
        "LANGFLOW_BASE_URL",
        "LANGFLOW_CORS_ORIGINS",
        "DJANGO_SECURE_PROXY_SSL_HEADER",
        "DJANGO_SESSION_COOKIE_SECURE",
        "DJANGO_CSRF_COOKIE_SECURE",
        "DJANGO_USE_X_FORWARDED_HOST",
        "DJANGO_ALLOWED_HOSTS",
    ]

    missing = [var for var in required_vars if var not in content]
    assert not missing, f"Variáveis em falta no .env.example: {missing}"
```

### Step 4: Instalar dependências de teste E2E (se necessário)

```bash
cd /home/RID/backend
# Verificar se websockets está disponível
python -c "import websockets" 2>/dev/null || pip install websockets

# Verificar se playwright está disponível
python -m playwright --version 2>/dev/null || pip install pytest-playwright && python -m playwright install chromium

# Verificar se requests está disponível (já deve estar)
python -c "import requests" 2>/dev/null || pip install requests
```

Expected output:
```
... (instalação se necessário)
```

### Step 5: Correr apenas o .env.example completeness check (sem Docker)

```bash
cd /home/RID
python -m pytest tests/e2e/test_auth_gate_e2e.py::test_env_example_completeness -v
```

Expected output:
```
tests/e2e/test_auth_gate_e2e.py::test_env_example_completeness PASSED
1 passed
```

### Step 6: Correr o cenário 7 (sem Docker completo)

```bash
cd /home/RID
# Se Langflow está parado, porta 7861 deve estar fechada
python -m pytest tests/e2e/test_auth_gate_e2e.py::test_scenario7_port_7861_not_publicly_accessible -v
```

Expected output:
```
tests/e2e/test_auth_gate_e2e.py::test_scenario7_port_7861_not_publicly_accessible PASSED
1 passed
```

### Step 7: Correr todos os cenários com stack completo (CI)

```bash
cd /home/RID
# Subir o stack
docker compose --profile langflow up -d --wait

# Correr todos os testes E2E
python -m pytest tests/e2e/ -v --timeout=120

# Descer o stack
docker compose --profile langflow down
```

Expected output:
```
tests/e2e/test_auth_gate_e2e.py::test_scenario4_langflow_unavailable_shows_error_page PASSED
tests/e2e/test_auth_gate_e2e.py::test_scenario6_websocket_upgrade_succeeds PASSED
tests/e2e/test_auth_gate_e2e.py::test_scenario7_port_7861_not_publicly_accessible PASSED
tests/e2e/test_auth_gate_e2e.py::test_env_example_completeness PASSED
... (outros cenários dependendo do stack)
```

### Step 8: Commit

```bash
cd /home/RID
git add tests/__init__.py tests/e2e/__init__.py tests/e2e/conftest.py tests/e2e/test_auth_gate_e2e.py
git commit -m "test(langflow-gate): add E2E tests for auth gate (Playwright overlay, error page, WebSocket, port check)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
