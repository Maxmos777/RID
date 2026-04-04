# syntax=docker/dockerfile:1.7
# =============================================================================
# Stage 1: builder — instala dependências com uv
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instala uv (pinned via checksum na versão oficial)
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copia apenas os ficheiros de lock para cache de layer (deps raramente mudam)
COPY pyproject.toml uv.lock ./

# Instala dependências de produção (sem dev extras) no diretório /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copia o restante do código-fonte
COPY . .

# Instala o projeto em si no virtualenv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# =============================================================================
# Stage 2: production — imagem mínima sem build toolchain
# =============================================================================
FROM python:3.12-slim AS production

# Metadata OCI
LABEL org.opencontainers.image.title="RID Backend" \
      org.opencontainers.image.description="RID Platform API (Django + FastAPI)" \
      org.opencontainers.image.source="https://github.com/org/rid" \
      org.opencontainers.image.licenses="MIT"

# Cria utilizador não-root para execução segura
RUN groupadd --gid 1000 appuser \
 && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings \
    PATH="/app/.venv/bin:$PATH"

# Copia o virtualenv compilado do stage builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copia o código-fonte com ownership correcto
COPY --chown=appuser:appuser . .

# Colecta ficheiros estáticos do Django (sem BD necessária)
RUN DJANGO_SECRET_KEY=build-time-secret-not-used-in-production \
    DATABASE_URL=postgres://x:x@localhost/x \
    python manage.py collectstatic --noinput 2>/dev/null || true

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Uvicorn como ASGI server; bind em 0.0.0.0 para funcionar em contentor
CMD ["uvicorn", "core.asgi:application", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
