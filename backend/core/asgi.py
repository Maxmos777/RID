"""
ASGI config for RID project.

FastAPI is mounted at /api using raw ASGI dispatch so Django's
TenantMainMiddleware is unaffected.

Dispatch logic:
  - lifespan  -> FastAPI (startup/shutdown hooks must run)
  - websocket -> route by path prefix
  - http      -> route by path prefix

Path routing:
  /api  ou  /api/*  -> FastAPI
  tudo o resto      -> Django
"""
from __future__ import annotations
import os
from typing import Any, Callable, Awaitable

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.asgi import get_asgi_application

django_app = get_asgi_application()

from api.main import create_app  # noqa: E402 -- must import after django setup

fastapi_app = create_app()


Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]

_API_PREFIX = "/api"


async def application(scope: Scope, receive: Receive, send: Send) -> None:
    """
    Root ASGI application.

    Routes /api and /api/* to FastAPI, everything else to Django.
    Lifespan events always go to FastAPI so startup/shutdown hooks run.
    """
    scope_type: str = scope.get("type", "http")
    path: str = scope.get("path", "")

    if scope_type == "lifespan":
        await fastapi_app(scope, receive, send)
    elif path == _API_PREFIX or path.startswith(_API_PREFIX + "/"):
        await fastapi_app(scope, receive, send)
    else:
        await django_app(scope, receive, send)
