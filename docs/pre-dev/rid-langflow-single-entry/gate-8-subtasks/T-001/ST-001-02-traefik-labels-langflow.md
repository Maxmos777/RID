# ST-001-02: Labels Traefik no serviço Langflow (forwardAuth + WebSocket)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Adicionar labels Traefik ao serviço `langflow` no `docker-compose.yml` para: router `PathPrefix('/flows')`, middleware `rid-auth` (forwardAuth → `/internal/auth-check/`), middleware `langflow-ws` (headers WebSocket), remover a porta pública `7861:7860`, e actualizar variáveis de ambiente `LANGFLOW_BASE_URL` e `LANGFLOW_CORS_ORIGINS`.

## Prerequisites

```bash
# ST-001-01 deve estar completo — Traefik service existe
grep -n "rid-traefik" /home/RID/docker-compose.yml
# Expected output: linha com container_name: rid-traefik

# Porta 7861 ainda existe (será removida neste subtask)
grep -n "7861" /home/RID/docker-compose.yml
# Expected output: linha com "7861:7860"

# docker compose config valida
cd /home/RID && docker compose config --quiet && echo "OK"
# Expected output: OK
```

## Files

- **Modify:** `docker-compose.yml` (serviço `langflow`: remover ports, adicionar labels e env vars)

## Steps

### Step 1: Escrever o teste de validação (RED)

```bash
cat > /tmp/test_langflow_labels.sh << 'EOF'
#!/bin/bash
set -e

CONFIG=$(docker compose -f /home/RID/docker-compose.yml config)

echo "=== Test: porta 7861 removida ==="
echo "$CONFIG" | grep "7861" && { echo "FAIL: porta 7861 ainda presente"; exit 1; } || echo "OK: 7861 não encontrada"

echo "=== Test: traefik.enable=true no langflow ==="
echo "$CONFIG" | grep "traefik.enable=true" | grep -q "true" || { echo "FAIL: traefik.enable=true não encontrado"; exit 1; }

echo "=== Test: forwardAuth address ==="
echo "$CONFIG" | grep -q "rid-auth.forwardauth.address" || { echo "FAIL: forwardauth.address não encontrado"; exit 1; }

echo "=== Test: trustForwardHeader ==="
echo "$CONFIG" | grep -q "trustForwardHeader=true" || { echo "FAIL: trustForwardHeader não encontrado"; exit 1; }

echo "=== Test: WebSocket middleware ==="
echo "$CONFIG" | grep -q "langflow-ws" || { echo "FAIL: langflow-ws middleware não encontrado"; exit 1; }

echo "=== Test: PathPrefix /flows ==="
echo "$CONFIG" | grep -q "PathPrefix" || { echo "FAIL: PathPrefix não encontrado"; exit 1; }

echo "=== Test: LANGFLOW_BASE_URL interno ==="
echo "$CONFIG" | grep -q "langflow:7860" || { echo "FAIL: LANGFLOW_BASE_URL interno não encontrado"; exit 1; }

echo "ALL TESTS PASSED"
EOF
chmod +x /tmp/test_langflow_labels.sh
bash /tmp/test_langflow_labels.sh
```

Expected output:
```
=== Test: porta 7861 removida ===
      - 7861:7860
FAIL: porta 7861 ainda presente
```

### Step 2: Modificar o serviço `langflow` no docker-compose.yml

No serviço `langflow`, fazer as seguintes alterações:

**Remover:**
```yaml
    ports:
      - "7861:7860"   # host:7861 -> container:7860 (evita conflito com processo local na 7860)
```

**Adicionar ao bloco `environment:`** (após as variáveis existentes):
```yaml
      LANGFLOW_BASE_URL: "http://langflow:7860"
      LANGFLOW_CORS_ORIGINS: "${LANGFLOW_CORS_ORIGINS:-https://app.rid.example.com}"
```

**Adicionar bloco `labels:` após `networks:`**:
```yaml
    labels:
      - "traefik.enable=true"
      # Router: captura /flows e sub-paths (incluindo WebSocket)
      - "traefik.http.routers.langflow.rule=PathPrefix(`/flows`)"
      - "traefik.http.routers.langflow.entrypoints=web"
      - "traefik.http.routers.langflow.middlewares=rid-auth@docker,langflow-ws@docker"
      # Serviço interno — porta nativa do container Langflow
      - "traefik.http.services.langflow.loadbalancer.server.port=7860"
      # Middleware forwardAuth — valida sessão via Django antes de encaminhar
      - "traefik.http.middlewares.rid-auth.forwardauth.address=http://backend:8000/internal/auth-check/"
      - "traefik.http.middlewares.rid-auth.forwardauth.trustForwardHeader=true"
      - "traefik.http.middlewares.rid-auth.forwardauth.authResponseHeaders=X-Auth-User,X-Auth-Tenant"
      # Middleware WebSocket — passa headers Upgrade e Connection
      - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Connection=keep-alive, Upgrade"
      - "traefik.http.middlewares.langflow-ws.headers.customrequestheaders.Upgrade=websocket"
```

### Step 3: Validar o YAML

```bash
cd /home/RID && docker compose config --quiet && echo "YAML válido"
```

Expected output:
```
YAML válido
```

### Step 4: Correr os testes (GREEN)

```bash
bash /tmp/test_langflow_labels.sh
```

Expected output:
```
=== Test: porta 7861 removida ===
OK: 7861 não encontrada
=== Test: traefik.enable=true no langflow ===
=== Test: forwardAuth address ===
=== Test: trustForwardHeader ===
=== Test: WebSocket middleware ===
=== Test: PathPrefix /flows ===
=== Test: LANGFLOW_BASE_URL interno ===
ALL TESTS PASSED
```

### Step 5: Commit

```bash
cd /home/RID
git add docker-compose.yml
git commit -m "feat(langflow-gate): add Traefik labels to langflow service, remove public port 7861"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
