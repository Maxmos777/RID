# =============================================================================
# RID Platform — Makefile raiz
# Adaptado para monorepo Python (uv) seguindo Ring DevOps Standards.
# =============================================================================

DOCKER_CMD := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)
COMPOSE_FILE := docker-compose.yml
BACKEND_DIR := ./backend

# -----------------------------------------------------------------------------
# Ajuda
# -----------------------------------------------------------------------------
.PHONY: help
help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
.PHONY: set-env
set-env: ## Copia .env.example → .env (não sobrepõe se já existir)
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
	  cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
	  echo "[ok] .env criado em $(BACKEND_DIR)"; \
	else \
	  echo "[skip] $(BACKEND_DIR)/.env já existe"; \
	fi

.PHONY: dev-setup
dev-setup: ## Instala ferramentas de desenvolvimento locais
	@command -v uv >/dev/null 2>&1 || pip install uv
	@cd $(BACKEND_DIR) && uv sync
	@echo "[ok] Dependências de dev instaladas"

# -----------------------------------------------------------------------------
# Build
# -----------------------------------------------------------------------------
.PHONY: build
build: ## Constrói a imagem Docker do backend
	$(DOCKER_CMD) -f $(COMPOSE_FILE) build backend

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
.PHONY: up
up: ## Inicia todos os serviços em background
	$(DOCKER_CMD) -f $(COMPOSE_FILE) up -d

.PHONY: down
down: ## Para e remove todos os contentores
	$(DOCKER_CMD) -f $(COMPOSE_FILE) down

.PHONY: start
start: ## Inicia contentores existentes (sem recriar)
	$(DOCKER_CMD) -f $(COMPOSE_FILE) start

.PHONY: stop
stop: ## Para contentores sem remover
	$(DOCKER_CMD) -f $(COMPOSE_FILE) stop

.PHONY: restart
restart: stop start ## Reinicia todos os contentores

.PHONY: rebuild-up
rebuild-up: ## Reconstrói e reinicia os serviços
	$(DOCKER_CMD) -f $(COMPOSE_FILE) down
	$(DOCKER_CMD) -f $(COMPOSE_FILE) build --no-cache
	$(DOCKER_CMD) -f $(COMPOSE_FILE) up -d

.PHONY: logs
logs: ## Segue os logs de todos os serviços
	$(DOCKER_CMD) -f $(COMPOSE_FILE) logs -f

# -----------------------------------------------------------------------------
# Qualidade de código
# -----------------------------------------------------------------------------
.PHONY: lint
lint: ## Executa ruff linter no backend
	@cd $(BACKEND_DIR) && uv run ruff check . --fix
	@echo "[ok] Linting concluído"

.PHONY: format
format: ## Formata o código com ruff
	@cd $(BACKEND_DIR) && uv run ruff format .

# -----------------------------------------------------------------------------
# Testes
# -----------------------------------------------------------------------------
.PHONY: test
test: ## Executa todos os testes
	@cd $(BACKEND_DIR) && uv run pytest

.PHONY: test-unit
test-unit: ## Executa apenas testes unitários (mark=unit)
	@cd $(BACKEND_DIR) && uv run pytest -m unit -v

.PHONY: cover
cover: ## Gera relatório de cobertura de testes
	@cd $(BACKEND_DIR) && uv run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "[ok] Relatório de cobertura em $(BACKEND_DIR)/htmlcov/index.html"

# -----------------------------------------------------------------------------
# Base de dados (Django migrations)
# -----------------------------------------------------------------------------
.PHONY: migrate-up
migrate-up: ## Aplica todas as migrations pendentes
	@cd $(BACKEND_DIR) && uv run python manage.py migrate
	@echo "[ok] Migrations aplicadas"

.PHONY: migrate-down
migrate-down: ## Rollback da última migration (requer NAME=app)
	@if [ -z "$(NAME)" ]; then \
	  echo "Uso: make migrate-down NAME=<app_label>"; exit 1; \
	fi
	@cd $(BACKEND_DIR) && uv run python manage.py migrate $(NAME) zero

.PHONY: migrate-create
migrate-create: ## Cria nova migration (requer NAME=descrição)
	@if [ -z "$(NAME)" ]; then \
	  echo "Uso: make migrate-create NAME=<descrição>"; exit 1; \
	fi
	@cd $(BACKEND_DIR) && uv run python manage.py makemigrations --name $(NAME)

.PHONY: migrate-version
migrate-version: ## Mostra o estado actual das migrations
	@cd $(BACKEND_DIR) && uv run python manage.py showmigrations

# -----------------------------------------------------------------------------
# Documentação
# -----------------------------------------------------------------------------
.PHONY: generate-docs
generate-docs: ## Exporta o schema OpenAPI (requer servidor a correr)
	@cd $(BACKEND_DIR) && uv run python -c \
	  "import json; from api.main import create_app; print(json.dumps(create_app().openapi(), indent=2))" \
	  > docs/openapi.json
	@echo "[ok] Schema OpenAPI exportado para docs/openapi.json"
