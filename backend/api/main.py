"""
FastAPI application factory.

Mounted at /api/* by core/asgi.py. All routers are registered here.
Lifespan handles startup/shutdown without blocking the event loop.
Interactive docs only enabled in DEBUG mode.

SECURITY: CSRF protection via CsrfProtectMiddleware for state-changing
requests (POST, PUT, DELETE, PATCH). Validates X-CSRFToken header against
Django's csrftoken cookie.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import CsrfProtectMiddleware

logger = logging.getLogger(__name__)
_DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup — add initialisation here (e.g. warm connection pools)
    yield
    # Shutdown — cleanup here


def create_app() -> FastAPI:
    app = FastAPI(
        title="RID API",
        version="0.1.0",
        # Interactive docs only in development
        docs_url="/api/docs" if _DEBUG else None,
        redoc_url="/api/redoc" if _DEBUG else None,
        openapi_url="/api/openapi.json" if _DEBUG else None,
        lifespan=lifespan,
    )

    # SECURITY FIX #2: CSRF Protection Middleware
    # Validates X-CSRFToken header against csrftoken cookie for state-changing requests.
    # Skips CSRF checks for safe methods (GET, HEAD, OPTIONS, TRACE) by default.
    app.add_middleware(CsrfProtectMiddleware)
    logger.info("CsrfProtectMiddleware enabled for FastAPI routes")

    # CORS — allow local frontend dev servers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # React dev (CRA / Vite default alt)
            "http://localhost:5173",   # Vite default
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    from api.routers.langflow_auth import router as langflow_auth_router
    from api.routers.tenant import router as tenant_router
    from api.routers.langflow import router as langflow_router

    app.include_router(
        langflow_auth_router,
        prefix="/api/v1/langflow",
        tags=["langflow"],
    )
    app.include_router(tenant_router, prefix="/api/v1/tenants", tags=["tenants"])
    app.include_router(langflow_router, tags=["langflow-health"])

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
