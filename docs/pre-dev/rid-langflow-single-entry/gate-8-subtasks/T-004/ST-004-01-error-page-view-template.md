# ST-004-01: View Django e template HTML da Error Page (/flows/error/)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar a view Django `flows_error` em `backend/apps/accounts/views.py` e o template HTML `backend/templates/flows/error.html` com identidade RID, texto pt-BR, dois CTAs ("Tentar novamente" e "Voltar ao painel"), sem dependências de assets do Langflow.

## Prerequisites

```bash
# urls.py base existe
cat /home/RID/backend/core/urls.py
# Expected output: urlpatterns com app/, internal/auth-check/, accounts/, admin/

# Directório de templates existe
ls /home/RID/backend/templates/
# Expected output: directório com apps/

# Template settings configurado para BASE_DIR/templates
grep -n "DIRS.*templates" /home/RID/backend/core/settings.py
# Expected output: "DIRS": [BASE_DIR / "templates"]
```

## Files

- **Create:** `backend/templates/flows/error.html`
- **Modify:** `backend/apps/accounts/views.py` (adicionar `flows_error` view)
- **Modify:** `backend/core/urls.py` (adicionar route `/flows/error/`)
- **Test:** `backend/tests/test_flows_error_page.py`

## Steps

### Step 1: Escrever os testes (RED)

Criar `/home/RID/backend/tests/test_flows_error_page.py`:

```python
"""Testes para a Error Page Template — GET /flows/error/ (T-004)."""
from __future__ import annotations

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


class TestFlowsErrorPageView:
    """GET /flows/error/ deve responder 200 sem depender do Langflow."""

    @pytest.mark.django_db
    def test_returns_200(self, client):
        response = client.get("/flows/error/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_response_is_html(self, client):
        response = client.get("/flows/error/")
        assert "text/html" in response["Content-Type"]

    @pytest.mark.django_db
    def test_url_name_resolves(self):
        url = reverse("flows-error")
        assert url == "/flows/error/"

    @pytest.mark.django_db
    def test_response_fast_under_200ms(self, client):
        import time
        start = time.perf_counter()
        client.get("/flows/error/")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 200, f"Resposta demorou {elapsed_ms:.1f}ms (> 200ms)"


class TestFlowsErrorPageContent:
    """O template deve conter conteúdo correcto em pt-BR."""

    @pytest.mark.django_db
    def test_contains_tentar_novamente_cta(self, client):
        response = client.get("/flows/error/")
        assert b"Tentar novamente" in response.content

    @pytest.mark.django_db
    def test_contains_voltar_ao_painel_cta(self, client):
        response = client.get("/flows/error/")
        assert b"Voltar ao painel" in response.content

    @pytest.mark.django_db
    def test_no_langflow_port_reference(self, client):
        response = client.get("/flows/error/")
        assert b"7860" not in response.content
        assert b"7861" not in response.content
        assert b"langflow" not in response.content.lower()

    @pytest.mark.django_db
    def test_has_role_main(self, client):
        response = client.get("/flows/error/")
        assert b'role="main"' in response.content

    @pytest.mark.django_db
    def test_has_lang_ptbr(self, client):
        response = client.get("/flows/error/")
        assert b'lang="pt-BR"' in response.content

    @pytest.mark.django_db
    def test_has_aria_labels_on_ctas(self, client):
        response = client.get("/flows/error/")
        assert b"aria-label" in response.content
```

### Step 2: Correr para confirmar que falha (RED)

```bash
cd /home/RID/backend
python -m pytest tests/test_flows_error_page.py -v 2>&1 | head -20
```

Expected output:
```
FAILED tests/test_flows_error_page.py::TestFlowsErrorPageView::test_returns_200 - AssertionError: assert 404 == 200
```

### Step 3: Criar o template HTML

Criar o directório e o template:

```bash
mkdir -p /home/RID/backend/templates/flows
```

Criar `/home/RID/backend/templates/flows/error.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Editor indisponível — RID</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f4f6f9;
      color: #1a1a2e;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }

    .card {
      background: #ffffff;
      border-radius: 8px;
      box-shadow: 0 2px 16px rgba(0,0,0,0.10);
      padding: 2.5rem 2rem;
      max-width: 480px;
      width: 100%;
      text-align: center;
    }

    .icon {
      font-size: 3rem;
      margin-bottom: 1rem;
      color: #e53e3e;
    }

    h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 0.75rem;
    }

    .description {
      font-size: 1rem;
      color: #4a5568;
      line-height: 1.6;
      margin-bottom: 2rem;
    }

    .actions {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    /* Botão primário — contraste >= 4.5:1 (#fff sobre #1a56db) */
    .btn-primary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: #1a56db;
      color: #ffffff;
      border: none;
      border-radius: 6px;
      padding: 0.875rem 1.5rem;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      min-height: 44px; /* WCAG 2.1 AA touch target */
      min-width: 44px;
      text-decoration: none;
      transition: background 0.15s;
    }

    .btn-primary:hover { background: #1644b8; }
    .btn-primary:focus-visible {
      outline: 3px solid #90cdf4;
      outline-offset: 2px;
    }
    .btn-primary:disabled {
      background: #718096;
      cursor: not-allowed;
    }

    /* Botão secundário — contraste >= 4.5:1 (#1a1a2e sobre #e2e8f0) */
    .btn-secondary {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: #e2e8f0;
      color: #1a1a2e;
      border: none;
      border-radius: 6px;
      padding: 0.875rem 1.5rem;
      font-size: 1rem;
      font-weight: 500;
      cursor: pointer;
      min-height: 44px;
      min-width: 44px;
      text-decoration: none;
      transition: background 0.15s;
    }

    .btn-secondary:hover { background: #cbd5e0; }
    .btn-secondary:focus-visible {
      outline: 3px solid #90cdf4;
      outline-offset: 2px;
    }

    .feedback {
      margin-top: 0.75rem;
      font-size: 0.9rem;
      color: #e53e3e;
      min-height: 1.4rem;
    }

    .loading-text { color: #718096; }
  </style>
</head>
<body>
  <main role="main" class="card">
    <div class="icon" aria-hidden="true">⚠️</div>

    <h1>Editor de fluxos indisponível</h1>

    <p class="description">
      O editor de fluxos está temporariamente indisponível. Isso pode ocorrer
      durante uma actualização ou reinicialização do sistema. Tente novamente
      em alguns instantes.
    </p>

    <div class="actions">
      <button
        id="btn-retry"
        class="btn-primary"
        aria-label="Tentar novamente abrir o editor de fluxos"
        onclick="retryFlows()"
      >
        Tentar novamente
      </button>

      <a
        href="/app/"
        class="btn-secondary"
        aria-label="Voltar ao painel da plataforma RID"
      >
        Voltar ao painel
      </a>
    </div>

    <p id="retry-feedback" class="feedback" aria-live="polite" role="status"></p>
  </main>

  <script>
    async function retryFlows() {
      const btn = document.getElementById('btn-retry');
      const feedback = document.getElementById('retry-feedback');

      btn.disabled = true;
      btn.textContent = 'Verificando…';
      btn.classList.add('loading-text');
      feedback.textContent = '';

      try {
        const response = await fetch('/flows/', {
          method: 'GET',
          credentials: 'same-origin',
          redirect: 'manual',
        });

        if (response.status === 200) {
          window.location.href = '/flows/';
        } else {
          feedback.textContent = 'Editor ainda indisponível. Tente novamente mais tarde.';
          btn.disabled = false;
          btn.textContent = 'Tentar novamente';
        }
      } catch {
        feedback.textContent = 'Erro de rede. Verifique a sua ligação e tente novamente.';
        btn.disabled = false;
        btn.textContent = 'Tentar novamente';
      }
    }
  </script>
</body>
</html>
```

### Step 4: Adicionar a view a apps/accounts/views.py

Em `/home/RID/backend/apps/accounts/views.py`, adicionar após os imports existentes e antes de `RockItDownSPA`:

```python
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def flows_error(request):
    """
    GET /flows/error/

    Página de erro com identidade RID — servida pelo Django quando o Langflow
    está indisponível (5xx/timeout upstream). Sem dependência de assets do Langflow.

    Response time target: < 200ms independentemente do estado do Langflow (TRD Component 4).
    """
    return render(request, "flows/error.html", status=200)
```

### Step 5: Registar a URL em core/urls.py

Editar `/home/RID/backend/core/urls.py` adicionando a import e o path:

```python
from apps.accounts.views import RockItDownSPA, flows_error

# Adicionar ao urlpatterns:
path("flows/error/", flows_error, name="flows-error"),
```

### Step 6: Correr os testes (GREEN)

```bash
cd /home/RID/backend
python -m pytest tests/test_flows_error_page.py -v
```

Expected output:
```
tests/test_flows_error_page.py::TestFlowsErrorPageView::test_returns_200 PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageView::test_response_is_html PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageView::test_url_name_resolves PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageView::test_response_fast_under_200ms PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_contains_tentar_novamente_cta PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_contains_voltar_ao_painel_cta PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_no_langflow_port_reference PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_has_role_main PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_has_lang_ptbr PASSED
tests/test_flows_error_page.py::TestFlowsErrorPageContent::test_has_aria_labels_on_ctas PASSED
10 passed
```

### Step 7: Commit

```bash
cd /home/RID
git add backend/templates/flows/error.html backend/apps/accounts/views.py backend/core/urls.py backend/tests/test_flows_error_page.py
git commit -m "feat(langflow-gate): add /flows/error/ Django view and branded error page template (pt-BR, WCAG 2.1 AA)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
