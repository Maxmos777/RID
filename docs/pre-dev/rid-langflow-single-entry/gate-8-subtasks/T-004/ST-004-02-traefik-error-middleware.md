# ST-004-02: Configurar middleware de erro Traefik (5xx → /flows/error/)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Adicionar o middleware `errors` do Traefik ao serviço `langflow` no `docker-compose.yml` para que respostas 5xx ou timeout do Langflow encaminhem o browser para `/flows/error/` (servida pelo Django), e actualizar os labels existentes do router `langflow`.

## Prerequisites

```bash
# ST-001-02 completo — labels Traefik no langflow existem
grep -n "rid-auth@docker" /home/RID/docker-compose.yml
# Expected output: linha com middlewares=rid-auth@docker,langflow-ws@docker

# ST-004-01 completo — /flows/error/ existe
cd /home/RID/backend && python -m pytest tests/test_flows_error_page.py -q
# Expected output: 10 passed

# docker compose config valida
cd /home/RID && docker compose config --quiet && echo "OK"
# Expected output: OK
```

## Files

- **Modify:** `docker-compose.yml` (adicionar middleware `langflow-errors` e actualizar labels do router)

## Steps

### Step 1: Escrever o teste de validação (RED)

```bash
cat > /tmp/test_traefik_errors_middleware.sh << 'EOF'
#!/bin/bash
set -e

CONFIG=$(docker compose -f /home/RID/docker-compose.yml config)

echo "=== Test: errors middleware definido ==="
echo "$CONFIG" | grep -q "langflow-errors" || { echo "FAIL: langflow-errors middleware não encontrado"; exit 1; }

echo "=== Test: errors middleware status 500-599 ==="
echo "$CONFIG" | grep -q "500-599" || { echo "FAIL: status 500-599 não configurado"; exit 1; }

echo "=== Test: errors middleware aponta para backend ==="
echo "$CONFIG" | grep -q "backend:8000/flows/error" || { echo "FAIL: URL /flows/error/ não encontrada no middleware"; exit 1; }

echo "=== Test: router langflow usa langflow-errors ==="
echo "$CONFIG" | grep "langflow.middlewares" | grep -q "langflow-errors" || { echo "FAIL: langflow-errors não aplicado ao router"; exit 1; }

echo "ALL TESTS PASSED"
EOF
chmod +x /tmp/test_traefik_errors_middleware.sh
bash /tmp/test_traefik_errors_middleware.sh
```

Expected output:
```
=== Test: errors middleware definido ===
FAIL: langflow-errors middleware não encontrado
```

### Step 2: Adicionar middleware de erros aos labels do serviço langflow

Em `/home/RID/docker-compose.yml`, no serviço `langflow`, localizar o label de middlewares:

```yaml
      - "traefik.http.routers.langflow.middlewares=rid-auth@docker,langflow-ws@docker"
```

Substituir por (adiciona `langflow-errors@docker`):

```yaml
      - "traefik.http.routers.langflow.middlewares=rid-auth@docker,langflow-ws@docker,langflow-errors@docker"
```

E adicionar os labels do middleware `langflow-errors` após os labels `langflow-ws` existentes:

```yaml
      # Middleware de erro: upstream 5xx/timeout → página de erro Django
      - "traefik.http.middlewares.langflow-errors.errors.status=500-599"
      - "traefik.http.middlewares.langflow-errors.errors.service=backend-error-svc@docker"
      - "traefik.http.middlewares.langflow-errors.errors.query=/flows/error/"
      # Serviço backend para servir a página de erro (porta 8000)
      - "traefik.http.services.backend-error-svc.loadbalancer.server.url=http://backend:8000"
```

### Step 3: Validar YAML

```bash
cd /home/RID && docker compose config --quiet && echo "YAML válido"
```

Expected output:
```
YAML válido
```

### Step 4: Correr os testes (GREEN)

```bash
bash /tmp/test_traefik_errors_middleware.sh
```

Expected output:
```
=== Test: errors middleware definido ===
=== Test: errors middleware status 500-599 ===
=== Test: errors middleware aponta para backend ===
=== Test: router langflow usa langflow-errors ===
ALL TESTS PASSED
```

### Step 5: Smoke test manual (opcional, requer stack a correr)

```bash
# Com o stack a correr e Langflow parado:
docker compose --profile langflow stop langflow
curl -I http://localhost/flows/
# Expected: 200 com conteúdo da error page do Django (não 502 genérico do Traefik)
docker compose --profile langflow start langflow
```

### Step 6: Commit

```bash
cd /home/RID
git add docker-compose.yml
git commit -m "feat(langflow-gate): configure Traefik errors middleware to route 5xx to /flows/error/"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
