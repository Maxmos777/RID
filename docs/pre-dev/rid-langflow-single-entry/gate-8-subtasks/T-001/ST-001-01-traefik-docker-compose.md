# ST-001-01: Adicionar serviço Traefik ao docker-compose.yml

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Adicionar o container Traefik v3.3.6 ao `docker-compose.yml` sob o perfil `langflow`, com entrypoints em :80 e :443, socket Docker montado em modo read-only, volume de certificados, e integrado à rede `rid-network`.

## Prerequisites

```bash
# Verificar que docker-compose.yml existe e tem a rede rid-network
grep -n "rid-network" /home/RID/docker-compose.yml
# Expected output: múltiplas linhas mencionando rid-network

# Verificar que não existe serviço traefik ainda
grep -n "traefik" /home/RID/docker-compose.yml
# Expected output: (vazio — sem resultado)

# Verificar que docker compose valida actualmente
cd /home/RID && docker compose config --quiet && echo "OK"
# Expected output: OK
```

## Files

- **Modify:** `docker-compose.yml` (adicionar serviço `traefik` após o serviço `langflow-pg-bootstrap`)
- **Create:** `certs/.gitkeep` (directório para certificados TLS)

## Steps

### Step 1: Escrever o teste de validação (RED)

```bash
cat > /tmp/test_traefik_compose.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Test: Traefik service exists ==="
docker compose -f /home/RID/docker-compose.yml config | grep -q "rid-traefik" || { echo "FAIL: rid-traefik container_name not found"; exit 1; }

echo "=== Test: Traefik image pinned ==="
docker compose -f /home/RID/docker-compose.yml config | grep -q "traefik:v3.3.6" || { echo "FAIL: traefik:v3.3.6 not found"; exit 1; }

echo "=== Test: Port 80 bound ==="
docker compose -f /home/RID/docker-compose.yml config | grep -q '"80:80"' || { echo "FAIL: port 80:80 not found"; exit 1; }

echo "=== Test: Docker socket read-only ==="
docker compose -f /home/RID/docker-compose.yml config | grep -q "/var/run/docker.sock" || { echo "FAIL: docker.sock mount not found"; exit 1; }

echo "=== Test: langflow profile ==="
docker compose -f /home/RID/docker-compose.yml config | grep -B5 "rid-traefik" | grep -q "langflow" || { echo "FAIL: traefik not in langflow profile"; exit 1; }

echo "ALL TESTS PASSED"
EOF
chmod +x /tmp/test_traefik_compose.sh
bash /tmp/test_traefik_compose.sh
```

Expected output:
```
=== Test: Traefik service exists ===
FAIL: rid-traefik container_name not found
```

### Step 2: Criar o directório de certificados

```bash
mkdir -p /home/RID/certs
touch /home/RID/certs/.gitkeep
```

Expected output:
```
(sem output — sucesso silencioso)
```

### Step 3: Adicionar o serviço Traefik ao docker-compose.yml

Abrir `/home/RID/docker-compose.yml` e adicionar o seguinte bloco imediatamente após o serviço `langflow-pg-bootstrap` (antes do serviço `langflow`):

```yaml
  # ---------------------------------------------------------------------------
  # Traefik v3.3.6 — edge router (auth gate para /flows/*)
  # ---------------------------------------------------------------------------
  traefik:
    image: traefik:v3.3.6
    container_name: rid-traefik
    restart: unless-stopped
    profiles:
      - langflow
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedByDefault=false"
      - "--providers.docker.network=rid-network"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--log.level=INFO"
      - "--accesslog=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./certs:/certs:ro"
    networks:
      - rid-network
    depends_on:
      backend:
        condition: service_started
```

### Step 4: Verificar que o YAML é válido (GREEN)

```bash
cd /home/RID && docker compose config --quiet && echo "YAML válido"
```

Expected output:
```
YAML válido
```

### Step 5: Correr os testes de validação

```bash
bash /tmp/test_traefik_compose.sh
```

Expected output:
```
=== Test: Traefik service exists ===
=== Test: Traefik image pinned ===
=== Test: Port 80 bound ===
=== Test: Docker socket read-only ===
=== Test: langflow profile ===
ALL TESTS PASSED
```

### Step 6: Commit

```bash
cd /home/RID
git add docker-compose.yml certs/.gitkeep
git commit -m "feat(langflow-gate): add Traefik v3.3.6 service to docker-compose under langflow profile"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
# ou
git checkout -- docker-compose.yml
rm -rf certs/
```
