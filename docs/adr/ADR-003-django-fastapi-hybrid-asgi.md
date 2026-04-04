# ADR-003 — Arquitectura híbrida Django + FastAPI via ASGI num mesmo processo

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:backend-engineer-typescript
**Revisores:** ring:governance-specialist
**Contexto de código:** `core/asgi.py`, `api/main.py`

---

## Contexto

O projecto precisa de:
1. **Django** para: admin, ORM, migrações, `django-tenants`, `django-allauth`, sistema de templates, gestão de sessões.
2. **API REST** com: documentação OpenAPI automática, tipagem de requests/responses, validação via Pydantic, dependências injectáveis, suporte a SSE (Server-Sent Events) para streaming Langflow.

A alternativa natural seria Django REST Framework (DRF), mas o DRF não gera OpenAPI moderno, não suporta SSE nativamente, e tem tipagem manual. FastAPI resolve todos estes pontos e é o standard para APIs Python async modernas.

O desafio é que `django-tenants` usa um middleware ASGI (`TenantMainMiddleware`) que precisa de interceptar *todos* os requests Django para definir o schema correcto — mas este middleware não deve envolver o stack FastAPI (que tem a sua própria resolução de tenant via `get_current_tenant`).

## Decisão

Corremos Django e FastAPI **no mesmo processo Python**, com dispatch ASGI manual em `core/asgi.py`:
- `lifespan` → FastAPI (gestão de startup/shutdown hooks)
- `/api` e `/api/*` → FastAPI (rotas REST)
- Tudo o resto → Django (admin, allauth, templates, websockets Django)

```python
# core/asgi.py:50
elif path == _API_PREFIX or path.startswith(_API_PREFIX + "/"):
    await fastapi_app(scope, receive, send)
else:
    await django_app(scope, receive, send)
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Django REST Framework (DRF) | Sem OpenAPI moderno, sem SSE nativo, tipagem manual, sem dependency injection. Migração futura para FastAPI seria mais custosa do que integrar agora. |
| Dois processos separados (Django API + FastAPI API) | Duplicação da camada de tenant resolution, dois serviços para orquestrar, comunicação inter-processo, sessões não partilhadas. Complexidade operacional sem benefício claro nesta fase. |
| FastAPI como serviço externo ao Django | Django faria chamadas HTTP para FastAPI. Round-trip network em cada request de autenticação/dados, sem partilha de conexões de BD, dupla gestão de migrações. |
| Django Ninja (FastAPI-like dentro de Django) | Mais integrado com Django, mas ecossistema mais pequeno, sem suporte completo a SSE, e bloqueia migração futura para FastAPI puro se necessário. |
| Migrar tudo para FastAPI (sem Django) | Perda do `django-tenants` (migrações automáticas por schema), admin Django, `django-allauth`. Reescrita de infraestrutura madura sem benefício imediato. |

## Consequências Positivas

- Django e FastAPI partilham o mesmo processo: sem chamadas HTTP inter-processo, sem duplicação de conexões de BD.
- `django-tenants` funciona para Django sem interferência com FastAPI.
- Documentação OpenAPI automática em `/api/docs` (modo DEBUG).
- Suporte nativo a SSE no FastAPI para streaming de resultados Langflow.
- Validação de requests via Pydantic com tipos explícitos.
- Uvicorn serve ambos com um único `gunicorn -k uvicorn.workers.UvicornWorker core.asgi:application`.

## Consequências Negativas / Trade-offs

- **Dois paradigmas no mesmo repositório:** engenheiros precisam de conhecer tanto Django (views, ORM, signals, middleware) como FastAPI (dependencies, routers, Pydantic). Onboarding mais complexo.
- **Resolução de tenant duplicada:** Django usa `TenantMainMiddleware` (automática), FastAPI usa `get_current_tenant` (injectável). Devem ser mantidas em sync se a lógica de resolução mudar.
- **`lifespan` exclusivo ao FastAPI:** o Django não tem hooks de lifespan equivalentes nesta configuração. Qualquer startup/shutdown hook Django precisa de ser registado via FastAPI `@asynccontextmanager lifespan`.
- **`/api` sem trailing slash:** requests a `/api` sem barra precisam de tratamento explícito (`path == _API_PREFIX`) — detalhe que causou bug inicial e foi documentado no ADR Impact.

## Compliance

```bash
# Verificar que o dispatch ASGI cobre /api sem barra
grep -n "_API_PREFIX" /home/RID/backend/core/asgi.py
# Expected: _API_PREFIX = "/api" e condição com path == _API_PREFIX

# Verificar que FastAPI só é instanciado após django setup
grep -n "create_app\|get_asgi_application" /home/RID/backend/core/asgi.py
# Expected: get_asgi_application() antes de create_app()

# Teste de routing
cd /home/RID/backend && . .venv/bin/activate && pytest tests/test_health.py::test_api_prefix_routes_to_fastapi_not_django -v
```

## Referências

- `core/asgi.py` — implementação do dispatcher
- `api/main.py` — factory FastAPI (`create_app`)
- `tests/test_health.py:18-22` — teste de routing FastAPI vs Django
- [ASGI spec](https://asgi.readthedocs.io/en/latest/specs/main.html) — especificação de `scope.type` e `scope.path`
- [django-tenants TenantMainMiddleware](https://github.com/django-tenants/django-tenants/blob/master/django_tenants/middleware/main.py) — middleware que não deve envolver FastAPI
