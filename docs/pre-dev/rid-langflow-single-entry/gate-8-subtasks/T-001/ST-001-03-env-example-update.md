# ST-001-03: Actualizar .env.example com variáveis de infraestrutura Traefik/Langflow

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Actualizar o ficheiro `.env.example` (ou equivalente) com as variáveis novas e alteradas introduzidas pela integração Traefik — `LANGFLOW_BASE_URL`, `LANGFLOW_CORS_ORIGINS`, `LANGFLOW_DB_PASSWORD` — e documentar o comportamento esperado de cada uma com comentários inline.

## Prerequisites

```bash
# Verificar que ST-001-01 e ST-001-02 estão completos
grep -n "langflow:7860" /home/RID/docker-compose.yml
# Expected output: linha com LANGFLOW_BASE_URL: "http://langflow:7860"

# Localizar o .env.example existente
find /home/RID -name ".env.example" -not -path "*/.venv/*" | head -5
# Expected output: /home/RID/backend/.env.example (ou path equivalente)
```

## Files

- **Modify:** `backend/.env.example` (adicionar secção de variáveis Traefik/Langflow)

## Steps

### Step 1: Escrever o teste (RED)

```bash
cat > /tmp/test_env_example.sh << 'EOF'
#!/bin/bash
set -e

ENV_FILE="/home/RID/backend/.env.example"

if [ ! -f "$ENV_FILE" ]; then
  echo "FAIL: $ENV_FILE não existe"
  exit 1
fi

echo "=== Test: LANGFLOW_BASE_URL documentado ==="
grep -q "LANGFLOW_BASE_URL" "$ENV_FILE" || { echo "FAIL: LANGFLOW_BASE_URL não encontrado em .env.example"; exit 1; }

echo "=== Test: LANGFLOW_CORS_ORIGINS documentado ==="
grep -q "LANGFLOW_CORS_ORIGINS" "$ENV_FILE" || { echo "FAIL: LANGFLOW_CORS_ORIGINS não encontrado em .env.example"; exit 1; }

echo "=== Test: comentário explicativo presente ==="
grep -q "langflow:7860" "$ENV_FILE" || { echo "FAIL: valor interno langflow:7860 não documentado"; exit 1; }

echo "ALL TESTS PASSED"
EOF
chmod +x /tmp/test_env_example.sh
bash /tmp/test_env_example.sh
```

Expected output:
```
=== Test: LANGFLOW_BASE_URL documentado ===
FAIL: LANGFLOW_BASE_URL não encontrado em .env.example
```

(ou, se o ficheiro não existir: `FAIL: /home/RID/backend/.env.example não existe`)

### Step 2: Localizar e ler o .env.example existente

```bash
find /home/RID -name ".env.example" -not -path "*/.venv/*"
```

Expected output: path do ficheiro existente (ex.: `/home/RID/backend/.env.example`)

Se o ficheiro não existir, criá-lo:
```bash
touch /home/RID/backend/.env.example
```

### Step 3: Adicionar secção de variáveis Traefik/Langflow ao .env.example

Adicionar ao final do ficheiro `/home/RID/backend/.env.example`:

```dotenv
# =============================================================================
# Traefik Auth Gate — rid-langflow-single-entry
# =============================================================================

# URL interna do Langflow (sem porta pública após remoção de 7861:7860).
# Em Docker Compose: http://langflow:7860 (hostname do container na rede rid-network).
# Em desenvolvimento local sem Docker: http://localhost:7860
LANGFLOW_BASE_URL=http://langflow:7860

# Origens CORS permitidas pelo Langflow.
# Deve corresponder ao domínio da plataforma RID acessado pelo browser (via Traefik).
# Em produção: https://app.rid.example.com
# Em desenvolvimento local: http://localhost:5173 (ou porta do Vite)
LANGFLOW_CORS_ORIGINS=https://app.rid.example.com
```

### Step 4: Correr os testes (GREEN)

```bash
bash /tmp/test_env_example.sh
```

Expected output:
```
=== Test: LANGFLOW_BASE_URL documentado ===
=== Test: LANGFLOW_CORS_ORIGINS documentado ===
=== Test: comentário explicativo presente ===
ALL TESTS PASSED
```

### Step 5: Commit

```bash
cd /home/RID
git add backend/.env.example
git commit -m "feat(langflow-gate): document Traefik/Langflow env vars in .env.example"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
