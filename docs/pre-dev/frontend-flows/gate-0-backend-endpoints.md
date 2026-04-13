---
feature: frontend-flows
gate: 0
type: backend-endpoints-research
date: 2026-04-11
status: final
title: GATE 0 — Backend Endpoints Mapping (Langflow + RID)
---

# Backend Endpoints Mapping — Langflow v1.8.3 + RID MVP

## Objetivo

Documentar todos os endpoints que o MVP de Frontend Flows precisa, tanto do Langflow quanto da RID backend, para implementação completa do dashboard.

---

## 1. Endpoints Langflow v1.8.3 (Internal)

### 1.1 Flows API (Principal)

#### GET /api/v1/projects/{workspace_id}/flows/

**Descrição:** Listar todos os flows de um workspace

| Campo | Valor |
|-------|-------|
| **HTTP Method** | GET |
| **Path** | `/api/v1/projects/{workspace_id}/flows/` |
| **Base URL** | `http://langflow:7860` (interno Docker) |
| **Autenticação** | Header: `x-api-key: {service_api_key}` |
| **Body** | Nenhum (GET request) |

**Path Parameters:**
- `workspace_id` (UUID): ID do workspace/project Langflow

**Query Parameters (Hipótese):**
```
?limit=50      # Limite de flows por página (desconhecido)
?skip=0        # Offset para paginação (desconhecido)
?sort=-updated_at  # Ordenação (desconhecido)
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Customer Support Bot",
      "description": "Chatbot para suporte",
      "updated_at": "2026-04-11T14:30:00Z",
      "created_at": "2026-03-15T09:15:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Sucesso (array pode estar vazio)
- `401 Unauthorized`: x-api-key inválida
- `403 Forbidden`: Sem permissão
- `404 Not Found`: workspace_id inválido
- `500 Server Error`: Erro Langflow

**Usado Por:** Frontend (via RID backend proxy)

**MVP Status:** ✅ CONFIRMADO (Q1 RESPONDIDA)

---

### 1.2 Projects/Workspaces API (Suporte)

#### GET /api/v1/projects/

**Descrição:** Listar projetos/workspaces (opcional para MVP)

| Campo | Valor |
|-------|-------|
| **HTTP Method** | GET |
| **Path** | `/api/v1/projects/` |
| **Autenticação** | `x-api-key` header |

**Response Schema:**
```json
{
  "data": [
    {
      "id": "7c8d9e0f-1234-5678-90ab-cdefg1234567",
      "name": "Starter Project",
      "description": "...",
      "created_at": "2026-03-15T09:15:00Z"
    }
  ]
}
```

**Usado Por:** Backend (validation; confirmar workspace existe)

**MVP Status:** ⏳ OPCIONAL (Phase 2)

---

### 1.3 Flow Execution (Suporte)

#### POST /api/v1/run/{flow_id}

**Descrição:** Executar um flow (para future chat interface)

| Campo | Valor |
|-------|-------|
| **HTTP Method** | POST |
| **Path** | `/api/v1/run/{flow_id}` |
| **Body** | `{ "input": "...", "variables": {...} }` |

**MVP Status:** ❌ OUT OF SCOPE (Phase 2)

---

## 2. Endpoints RID Backend (FastAPI)

### 2.1 Flows List Endpoint (MVP)

#### GET /api/v1/langflow/flows/list

**Descrição:** BFF proxy para listar flows (seguro, multi-tenant)

| Campo | Valor |
|-------|-------|
| **HTTP Method** | GET |
| **Path** | `/api/v1/langflow/flows/list` |
| **Autenticação** | Django session (credentials: include) |
| **Headers** | `X-CSRFToken`, `X-Tenant-Id` (opcional) |

**Request Example:**
```
GET /api/v1/langflow/flows/list HTTP/1.1
Host: localhost:8000
Cookie: sessionid={django_session_id}
X-CSRFToken: {csrf_token}
X-Tenant-Id: {customer_public_tenant_id}  # optional
```

**Backend Logic:**
1. Validate Django session (get_current_user)
2. Resolve tenant (via X-Tenant-Id or Host header)
3. Validate TenantMembership (user is member of tenant)
4. Fetch Customer (get langflow_workspace_id + langflow_service_api_key)
5. Call Langflow API (GET /api/v1/projects/{workspace_id}/flows/)
6. Transform response (FlowDTO[])
7. Return JSON

**Response (200 OK):**
```json
{
  "flows": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Customer Support Bot",
      "description": "Chatbot para suporte",
      "updated_at": "2026-04-11T14:30:00Z",
      "created_at": "2026-03-15T09:15:00Z"
    }
  ],
  "workspace_id": "7c8d9e0f-1234-5678-90ab-cdefg1234567",
  "total_count": 1
}
```

**Status Codes:**
- `200 OK`: Sucesso
- `401 Unauthorized`: Sessão expirada
- `403 Forbidden`: Sem acesso ao tenant
- `503 Service Unavailable`: Langflow indisponível / workspace não provisionado

**File Location:** `backend/api/routers/langflow_flows.py` (novo)

**MVP Status:** ✅ DESIGN APROVADO (implementar em GATE 4)

---

### 2.2 Auth Endpoints (MVP)

#### GET /api/v1/langflow/auth/session

**Descrição:** Validar sessão na inicialização da app

| Campo | Valor |
|-------|-------|
| **HTTP Method** | GET |
| **Path** | `/api/v1/langflow/auth/session` |
| **Autenticação** | Django session |

**Response (200 OK):**
```json
{
  "authenticated": true,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "username": "user"
  }
}
```

**MVP Status:** ✅ JÁ EXISTE (reutilizar)

---

#### POST /api/v1/langflow/auth/auto-login

**Descrição:** Obter credenciais auto-login para Langflow

| Campo | Valor |
|-------|-------|
| **HTTP Method** | POST |
| **Path** | `/api/v1/langflow/auth/auto-login` |
| **Autenticação** | Django session |

**Response:**
```json
{
  "langflow_user": "user@example.com",
  "langflow_password": "...",
  "redirect_url": "/flows/"
}
```

**MVP Status:** ✅ JÁ EXISTE (usada na navegação)

---

#### POST /api/v1/langflow/auth/refresh (Hipotético)

**Descrição:** Renovar access token (para session management)

| Campo | Valor |
|-------|-------|
| **HTTP Method** | POST |
| **Path** | `/api/v1/langflow/auth/refresh` |
| **Body** | `{}` (HttpOnly cookies do refresh token) |

**Response:**
```json
{
  "access_token": "new_token_...",
  "token_type": "bearer"
}
```

**MVP Status:** ⏳ VERIFICAR (pode ser passthrough ao Langflow)

---

### 2.3 Internal Auth Check (Traefik)

#### GET /internal/auth-check/

**Descrição:** Auth check endpoint para Traefik (forwardAuth)

| Campo | Valor |
|-------|-------|
| **HTTP Method** | GET |
| **Path** | `/internal/auth-check/` |
| **Headers** | Cookie (sessionid), X-Tenant-Id |

**Traefik Usage:**
```yaml
forwardAuth:
  address: http://backend:8000/internal/auth-check/
  trustForwardHeader: true
  authResponseHeaders:
    - X-Remote-User
    - X-Tenant-Id
```

**Response:**
- `200 OK`: Autenticado + tenant válido (forward request)
- `401 Unauthorized`: Sem sessão (redirect to /login)
- `403 Forbidden`: Tenant inválido (deny access)

**MVP Status:** ✅ JÁ EXISTE (ADR-012)

---

## 3. Endpoints RID Django (Complemento)

### 3.1 Session Endpoints

#### GET /api/session (Django)

**Descrição:** Validar sessão Django

**Response:**
```json
{
  "authenticated": true,
  "user": "user@example.com"
}
```

**MVP Status:** ✅ JÁ EXISTE (LoginRequiredMixin)

---

#### POST /login (Django)

**Descrição:** Login com credenciais

**Response:**
```json
{
  "authenticated": true,
  "session_id": "..."
}
```

**MVP Status:** ✅ JÁ EXISTE

---

## 4. Endpoints Summary Table

| Endpoint | Service | Método | Escopo | MVP |
|----------|---------|--------|--------|-----|
| `GET /api/v1/projects/{id}/flows/` | Langflow | GET | Lista flows | ✅ |
| `POST /api/v1/langflow/flows/list` | RID (BFF) | GET | Proxy seguro | ✅ NOVO |
| `GET /api/v1/langflow/auth/auto-login` | RID | POST | Navigate to editor | ✅ EXISTS |
| `GET /api/v1/langflow/auth/session` | RID | GET | Session validation | ✅ EXISTS |
| `GET /internal/auth-check/` | RID (Traefik) | GET | Auth gate | ✅ EXISTS |
| `POST /api/v1/langflow/auth/refresh` | RID | POST | Token refresh | ⏳ VERIFY |
| `POST /api/v1/run/{flow_id}` | Langflow | POST | Execute flow | ❌ Phase 2 |
| `GET /api/v1/projects/` | Langflow | GET | List workspaces | ❌ Phase 2 |

---

## 5. Authentication Flow (MVP)

```
┌─────────────────────────────────────────────────────┐
│ Frontend App Load                                   │
│ 1. GET /app/flows                                   │
│ 2. Django: Validate session (LoginRequiredMixin)   │
│ 3. Render React app (app-config injected)          │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ React Mount: useSessionRefresh()                    │
│ 1. Setup proactive token refresh (~54 min)         │
│ 2. Axios interceptor for 401/403 handling          │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Fetch Flows                                         │
│ GET /api/v1/langflow/flows/list                    │
│ (Axios with credentials: include)                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ RID Backend                                         │
│ 1. get_current_user (FastAPI dep) — validate      │
│ 2. get_current_tenant (middleware)                 │
│ 3. validate_tenant_membership (check user in team) │
│ 4. get_customer (retrieve langflow_workspace_id)   │
│ 5. call_langflow_api (x-api-key header)            │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Langflow (Internal)                                 │
│ GET /api/v1/projects/{workspace_id}/flows/         │
│ Header: x-api-key: {service_api_key}              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Response: JSON { data: [flows...] }                │
└─────────────────────────────────────────────────────┘
```

---

## 6. Implementation Checklist

### Backend (RID)
- [ ] `backend/api/routers/langflow_flows.py` — new endpoint
- [ ] `backend/api/schemas/flows.py` — FlowDTO, FlowsListResponse
- [ ] `backend/tests/test_langflow_flows_list.py` — integration tests
- [ ] Verify: Customer model has `langflow_workspace_id` + `langflow_service_api_key`
- [ ] Verify: TenantMembership validation logic

### Frontend (React)
- [ ] `src/api/axios-client.ts` — HTTP client with interceptors
- [ ] `src/hooks/useFlows.ts` — fetch flows hook
- [ ] `src/stores/authStore.ts` — Zustand store
- [ ] `src/hooks/useSessionRefresh.ts` — proactive refresh
- [ ] `src/components/FlowsList.tsx` — main component
- [ ] Tests: useFlows, useSessionRefresh, FlowsList

### Validation
- [ ] Spike task: Verify Langflow v1.8.3 endpoint in staging
- [ ] Verify: Query params for pagination (limit, skip)
- [ ] Verify: Response schema matches expected

---

## 7. Error Handling Strategy

### Langflow API Errors

```python
# backend/api/routers/langflow_flows.py
try:
    response = await client.get(
        f"{LANGFLOW_BASE_URL}/api/v1/projects/{workspace_id}/flows/",
        headers={"x-api-key": api_key},
        timeout=10.0
    )
    response.raise_for_status()
except httpx.TimeoutException:
    raise ServiceUnavailable("Langflow timeout")
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        raise NotFound("Workspace not found")
    if e.response.status_code == 401:
        raise Unauthorized("Invalid API key")
    raise ServiceUnavailable("Langflow unavailable")
```

### Frontend Error Handling (Axios Interceptor)

```typescript
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh
      await refreshToken();
    } else if (error.response?.status === 503) {
      // Show error: "Langflow unavailable, retry later"
    }
  }
);
```

---

## 8. References

### Files in RID
- `/home/RID/backend/api/services/langflow_client.py` — Langflow client patterns
- `/home/RID/backend/api/services/langflow_workspace.py` — Workspace provisioning
- `/home/RID/backend/api/routers/langflow_auth.py` — Auth endpoint patterns
- `/home/RID/docs/adr/ADR-009-langflow-integration.md` — Architecture decision

### External
- Langflow GitHub: https://github.com/langflow-ai/langflow/tree/main/src/backend
- Langflow API Docs: (check `/docs` endpoint in Langflow)

---

**Document Status: FINAL** ✅  
**Q1 Status: RESPONDIDA** ✅  
**Ready for: GATE 4 Implementation**
