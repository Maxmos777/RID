# ST-002-02: Documentar variáveis de proxy no .env.example

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Adicionar ao `backend/.env.example` as variáveis `DJANGO_SECURE_PROXY_SSL_HEADER`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, e `DJANGO_USE_X_FORWARDED_HOST` com comentários explicativos, para que qualquer operador saiba o que activar em staging/produção.

## Prerequisites

```bash
# ST-002-01 deve estar completo
grep -n "SECURE_PROXY_SSL_HEADER" /home/RID/backend/core/settings.py
# Expected output: linha com _proxy_ssl = os.getenv("DJANGO_SECURE_PROXY_SSL_HEADER"...)

# .env.example existe (criado ou já existente)
ls -la /home/RID/backend/.env.example 2>/dev/null || echo "não existe — criar"
```

## Files

- **Modify:** `backend/.env.example`

## Steps

### Step 1: Escrever o teste (RED)

```bash
cat > /tmp/test_env_proxy_vars.sh << 'EOF'
#!/bin/bash
set -e
FILE="/home/RID/backend/.env.example"

echo "=== Test: DJANGO_SECURE_PROXY_SSL_HEADER ==="
grep -q "DJANGO_SECURE_PROXY_SSL_HEADER" "$FILE" || { echo "FAIL"; exit 1; }

echo "=== Test: DJANGO_SESSION_COOKIE_SECURE ==="
grep -q "DJANGO_SESSION_COOKIE_SECURE" "$FILE" || { echo "FAIL"; exit 1; }

echo "=== Test: DJANGO_CSRF_COOKIE_SECURE ==="
grep -q "DJANGO_CSRF_COOKIE_SECURE" "$FILE" || { echo "FAIL"; exit 1; }

echo "=== Test: DJANGO_USE_X_FORWARDED_HOST ==="
grep -q "DJANGO_USE_X_FORWARDED_HOST" "$FILE" || { echo "FAIL"; exit 1; }

echo "=== Test: DJANGO_ALLOWED_HOSTS com backend ==="
grep -q "backend" "$FILE" || { echo "FAIL: 'backend' não documentado em ALLOWED_HOSTS"; exit 1; }

echo "ALL TESTS PASSED"
EOF
chmod +x /tmp/test_env_proxy_vars.sh
bash /tmp/test_env_proxy_vars.sh
```

Expected output:
```
=== Test: DJANGO_SECURE_PROXY_SSL_HEADER ===
FAIL
```

### Step 2: Adicionar secção ao .env.example

Adicionar ao ficheiro `/home/RID/backend/.env.example`:

```dotenv
# =============================================================================
# Django Proxy Header Settings — Traefik auth gate (T-002)
# =============================================================================
# Activar em staging e produção (quando Traefik está na frente do Django).
# Deixar em branco ou "false" em desenvolvimento local.

# Django reconhece HTTPS quando Traefik injeta X-Forwarded-Proto: https.
# Produção/staging: true | Desenvolvimento local: false (ou omitir)
DJANGO_SECURE_PROXY_SSL_HEADER=true

# Cookie de sessão apenas transmitido via HTTPS (Secure flag).
# Produção/staging: true | Desenvolvimento local: false
DJANGO_SESSION_COOKIE_SECURE=true

# Cookie CSRF apenas via HTTPS.
# Produção/staging: true | Desenvolvimento local: false
DJANGO_CSRF_COOKIE_SECURE=true

# TenantMainMiddleware usa X-Forwarded-Host para resolver tenant.
# Obrigatório quando Traefik está activo (forwardAuth sub-requests passam Host interno).
# Produção/staging: true | Desenvolvimento local: false (ou omitir)
DJANGO_USE_X_FORWARDED_HOST=true

# Hosts Django permitidos. 'backend' é necessário para sub-requests internos do Traefik.
# Formato: lista separada por vírgulas.
# Produção: app.rid.example.com,backend,localhost,127.0.0.1,testserver
DJANGO_ALLOWED_HOSTS=app.rid.example.com,backend,localhost,127.0.0.1,testserver
```

### Step 3: Correr o teste (GREEN)

```bash
bash /tmp/test_env_proxy_vars.sh
```

Expected output:
```
=== Test: DJANGO_SECURE_PROXY_SSL_HEADER ===
=== Test: DJANGO_SESSION_COOKIE_SECURE ===
=== Test: DJANGO_CSRF_COOKIE_SECURE ===
=== Test: DJANGO_USE_X_FORWARDED_HOST ===
=== Test: DJANGO_ALLOWED_HOSTS com backend ===
ALL TESTS PASSED
```

### Step 4: Commit

```bash
cd /home/RID
git add backend/.env.example
git commit -m "feat(langflow-gate): document Django proxy settings env vars in .env.example"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
