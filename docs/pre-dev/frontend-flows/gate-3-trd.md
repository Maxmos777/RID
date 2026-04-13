---
feature: frontend-flows
gate: 3
date: 2026-04-13
status: revised
topology:
  structure: mono-repo
  target_repo: /home/RID
  scope: frontend + backend
  api_pattern: bff
  arch_style: modular_monolith
  edge: reverse_proxy
  edge_router: traefik
revision_notes: |
  2026-04-13: Semantic alignment audit (GATE 2 vs GATE 3)
  - Added Feature 2 (Session Management: Zustand + Axios)
  - Added Feature 3 (React Router setup)
  - Added Feature 8 (Tailwind styling)
  - Added Feature 9 (Global error handling)
  - Split Feature 7 into 7a (unit/component) and 7b (integration/e2e)
  - Referenced src/types/stores.ts type contracts
  - Defined critical path and execution order
---

# TRD — Frontend Flows Dashboard MVP (Projeto Técnico)

## Resumo Executivo

Este documento especifica a arquitetura técnica para o MVP de Dashboard de Flows, cobrindo **9 features granulares** (F1-F9) mapeadas no GATE 2 Feature Map. Define:

1. **Feature 1:** Backend endpoint `/api/v1/langflow/flows/list` (seguro, multi-tenant)
2. **Feature 2:** Session management com Zustand stores + Axios interceptor + token refresh
3. **Feature 3:** React Router setup com protected routes
4. **Feature 4:** FlowsList component com grid, paginação, loading/error/empty states
5. **Feature 5:** Navigation segura ao Langflow editor via Traefik
6. **Feature 6:** Context persistence (sessionStorage) para UI state recovery
7. **Feature 7a:** Unit + component tests (parallelizável com Feature 4)
8. **Feature 7b:** Integration + E2E tests (após Feature 6)
9. **Feature 8:** Tailwind CSS styling (componentes, responsive design)
10. **Feature 9:** Global error handling strategy (ErrorBoundary, toast, retry)

**Conformidade:** ADR-001 through ADR-012, type contracts em `src/types/stores.ts`

**Critical Path:** F1 → F2 → F3 → F4 + F7a (parallel) → F5 → F6 → F7b → (F8, F9 concurrent)
**Wall-clock:** 15-22h with 2 engineers

---

## 0. Frontend Architecture & Routing (Feature 3)

### 0.1 React Router Setup

**Localização:** 
- `frontend/apps/rockitdown/src/main.tsx` — Wrap with BrowserRouter
- `frontend/apps/rockitdown/src/App.tsx` — Routes + Outlet
- `frontend/apps/rockitdown/src/components/ProtectedRoute.tsx` — Auth guard

**Responsabilidade:**
1. Initialize React Router v6.23.1
2. Define route tree with authentication guards
3. Render layout with sidebar + main content outlet

**main.tsx Refactor:**
```typescript
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

**App.tsx Routes:**
```typescript
import { Routes, Route, Outlet } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Sidebar } from './components/Sidebar';
import { FlowsPage } from './pages/FlowsPage';
import { AppConfig } from './types';

export function App({ config }: { config: AppConfig }) {
  return (
    <Routes>
      <Route path="/app" element={<ProtectedLayout config={config} />}>
        <Route path="flows" element={<FlowsPage config={config} />} />
        <Route path="dashboard" element={<div>Dashboard (Phase 2)</div>} />
      </Route>
    </Routes>
  );
}

function ProtectedLayout({ config }: { config: AppConfig }) {
  return (
    <ProtectedRoute config={config}>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </ProtectedRoute>
  );
}
```

**ProtectedRoute Component:**
```typescript
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useSessionRefresh } from '../hooks/useSessionRefresh';
import { AppConfig } from '../types';

export function ProtectedRoute({
  config,
  children
}: {
  config: AppConfig;
  children: React.ReactNode;
}) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  
  // Activate proactive session refresh (Feature 2)
  useSessionRefresh(config);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}
```

---

## 1. Especificação do Endpoint Backend

### 1.1 Endpoint: `GET /api/v1/langflow/flows/list`

**Localização:** `backend/api/routers/langflow_flows.py` (novo arquivo)

**Responsabilidade:** Listar todos os flows do workspace Langflow do tenant autenticado.

**Autenticação:** Sessão Django (usuário autenticado via `TenantAwareBackend`)

**Autorização:**
1. Usuário deve estar autenticado (sessão válida)
2. Usuário deve ser membro do tenant (TenantMembership validado)
3. Retorna apenas flows do workspace do customer

#### Request

```http
GET /api/v1/langflow/flows/list HTTP/1.1
Host: api.example.com
Cookie: sessionid=<django-session-id>
X-Tenant-Id: <customer-public-tenant-id>
Content-Type: application/json
```

**Headers Opcionais:**
- `X-Tenant-Id`: UUID do customer (resolve tenant via header; override Host header)
- Se não fornecido: resolver tenant via Host header (multi-tenant middleware)

#### Response (200 OK)

```json
{
  "flows": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Customer Support Bot",
      "description": "Chatbot para suporte ao cliente com NLP",
      "updated_at": "2026-04-11T14:30:00Z",
      "created_at": "2026-03-15T09:15:00Z"
    },
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Data Pipeline",
      "description": null,
      "updated_at": "2026-04-10T16:45:00Z",
      "created_at": "2026-04-01T10:00:00Z"
    }
  ],
  "workspace_id": "7c8d9e0f-1234-5678-90ab-cdefg1234567",
  "total_count": 2
}
```

#### Response (401 Unauthorized)

```json
{
  "detail": "Não autenticado. Por favor, faça login novamente."
}
```

**Quando:** Sessão Django ausente, expirada ou inválida.

#### Response (403 Forbidden)

```json
{
  "detail": "Acesso negado. Você não é membro deste workspace."
}
```

**Quando:** Usuário autenticado mas não é membro do tenant (TenantMembership missing).

#### Response (503 Service Unavailable)

```json
{
  "detail": "Langflow temporariamente indisponível. Tente novamente em alguns momentos.",
  "retry_after": 60
}
```

**Quando:**
- Customer não tem `langflow_workspace_id` provisionado (workspace 409 pending)
- Customer não tem `langflow_service_api_key` (missing credentials)
- Langflow API retorna 5xx ou timeout

---

### 1.2 Lógica Interna

**Pseudocódigo:**

```python
@router.get("/langflow/flows/list")
async def list_flows(
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)]
):
    """
    Listar flows do workspace Langflow do tenant autenticado.
    
    Fluxo de execução:
    1. Validar que usuário está autenticado (já garantido por Depends)
    2. Resolver tenant via X-Tenant-Id header ou Host header
    3. Validar que usuário é membro do tenant (TenantMembership)
    4. Recuperar Customer (schema_name = tenant.schema_name)
    5. Validar que Customer.langflow_workspace_id existe
    6. Validar que Customer.langflow_service_api_key existe
    7. Chamar Langflow API: GET /api/v1/projects/{workspace_id}/flows/
    8. Transformar resposta Langflow em FlowDTO[]
    9. Retornar JSON com metadata do workspace
    """
    
    # Resolução de tenant (middleware já fez, acessar do contexto)
    tenant = await get_current_tenant(request)
    
    # Validar membership
    is_member = await sync_to_async(
        TenantMembership.objects.filter(
            user=user,
            tenant=tenant
        ).exists,
        thread_sensitive=True
    )()
    if not is_member:
        raise PermissionDenied("Acesso negado ao tenant")
    
    # Recuperar credenciais do customer
    customer = await sync_to_async(
        Customer.objects.get,
        thread_sensitive=True
    )(schema_name=tenant.schema_name)
    
    workspace_id = customer.langflow_workspace_id
    api_key = customer.langflow_service_api_key
    
    if not workspace_id or not api_key:
        raise ServiceUnavailable(
            "Workspace Langflow não provisionado para este cliente"
        )
    
    # Chamar Langflow API
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{LANGFLOW_BASE_URL}/api/v1/projects/{workspace_id}/flows/",
                headers={"x-api-key": api_key}
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            raise ServiceUnavailable("Langflow timeout")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFound("Workspace Langflow não encontrado")
            if e.response.status_code >= 500:
                raise ServiceUnavailable("Langflow indisponível")
            raise
    
    # Transformar resposta
    langflow_data = response.json()
    langflow_flows = langflow_data.get("data", [])
    
    flows = [
        FlowDTO(
            id=f["id"],
            name=f["name"],
            description=f.get("description"),
            updated_at=parse_iso8601(f.get("updated_at")),
            created_at=parse_iso8601(f.get("created_at"))
        )
        for f in langflow_flows
    ]
    
    return FlowsListResponse(
        flows=flows,
        workspace_id=workspace_id,
        total_count=len(flows)
    )
```

---

### 1.3 Tipos (DTOs)

**Arquivo:** `backend/api/schemas/flows.py` (novo)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FlowDTO(BaseModel):
    """Representação de um Flow do Langflow."""
    id: str = Field(..., description="UUID único do flow no Langflow")
    name: str = Field(..., description="Nome do flow")
    description: Optional[str] = Field(
        None,
        description="Descrição opcional do flow"
    )
    updated_at: datetime = Field(..., description="Timestamp da última atualização")
    created_at: datetime = Field(..., description="Timestamp de criação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Customer Support Bot",
                "description": "Chatbot para suporte ao cliente",
                "updated_at": "2026-04-11T14:30:00Z",
                "created_at": "2026-03-15T09:15:00Z"
            }
        }

class FlowsListResponse(BaseModel):
    """Response do endpoint /api/v1/langflow/flows/list."""
    flows: list[FlowDTO] = Field(..., description="Array de flows")
    workspace_id: str = Field(..., description="UUID do workspace Langflow")
    total_count: int = Field(..., description="Total de flows no workspace")
```

---

### 1.4 Tratamento de Erros

| HTTP Status | Erro | Causa Raiz | Recovery |
|-------------|------|-----------|----------|
| **401** | Não autenticado | Sessão expirada, cookie inválido | Redirect para login |
| **403** | Forbidden | Usuário não é membro do tenant | Mostrar erro; escalar a admin |
| **404** | Workspace não encontrado | workspace_id inválido ou deletado | Provisionar nova workspace (Phase 2) |
| **503** | Service Unavailable | Langflow offline, credentials missing | Retry button; notificação operacional |
| **500** | Server Error | Erro interno (DB, parsing, etc.) | Log; retry button |

---

## 2. Arquitetura de Componentes Frontend

### 2.1 Estrutura de Pastas

```
frontend/apps/rockitdown/src/
├── components/
│   ├── FlowsList.tsx              # Componente principal (grid/list)
│   ├── FlowCard.tsx               # Card individual de flow
│   └── __tests__/
│       └── FlowsList.test.tsx     # Testes de FlowsList
├── hooks/
│   ├── useFlows.ts                # Hook: fetch flows from backend
│   ├── useFlowsContext.ts         # Hook: persist/restore UI state
│   └── __tests__/
│       ├── useFlows.test.ts       # Testes unitários
│       └── useFlowsContext.test.ts
├── types/
│   └── flows.ts                   # Interfaces locais (extends @rid/shared)
├── pages/
│   └── FlowsPage.tsx              # Page wrapper (layout)
├── __tests__/
│   └── flows-integration.test.tsx # Testes E2E
└── App.tsx                         # Updated com routing para /app/flows
```

---

### 2.2 Componentes & Hooks

#### `useFlows.ts` — Hook de Fetch

**Responsabilidade:** Buscar flows de `/api/v1/langflow/flows/list`, gerenciar loading/error states, cleanup.

```typescript
interface UseFlowsOptions {
  refetchInterval?: number;  // ms entre refetch automático (Phase 2)
}

interface UseFlowsReturn {
  flows: Flow[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useFlows(
  config: AppConfig,
  options: UseFlowsOptions = {}
): UseFlowsReturn {
  const [flows, setFlows] = useState<Flow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const fetchFlows = useCallback(async () => {
    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${config.api.base_url}/langflow/flows/list`,
        {
          method: 'GET',
          credentials: 'include',  // inclui sessão Django
          signal: abortControllerRef.current.signal,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': config.csrf_token
          }
        }
      );
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Sessão expirada. Por favor, faça login novamente.');
        }
        if (response.status === 403) {
          throw new Error('Você não tem acesso a este workspace.');
        }
        if (response.status === 503) {
          throw new Error('Langflow está temporariamente indisponível.');
        }
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json() as FlowsListResponse;
      setFlows(data.flows);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [config]);
  
  useEffect(() => {
    fetchFlows();
    
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchFlows]);
  
  return {
    flows,
    loading,
    error,
    refetch: fetchFlows
  };
}
```

---

#### `useFlowsContext.ts` — Hook de Persistência

**Responsabilidade:** Salvar/restaurar estado de UI (página, scroll) em sessionStorage com expiry.

```typescript
interface FlowsContext {
  currentPage: number;
  scrollPosition: number;
  timestamp: number;
}

const CONTEXT_KEY = 'flows_list_context';
const CONTEXT_TTL_MS = 30 * 60 * 1000;  // 30 minutos

export function useFlowsContext() {
  const save = useCallback((context: FlowsContext): void => {
    sessionStorage.setItem(CONTEXT_KEY, JSON.stringify(context));
  }, []);
  
  const restore = useCallback((): FlowsContext | null => {
    const saved = sessionStorage.getItem(CONTEXT_KEY);
    if (!saved) return null;
    
    try {
      const context = JSON.parse(saved) as FlowsContext;
      const isExpired = Date.now() - context.timestamp > CONTEXT_TTL_MS;
      
      if (isExpired) {
        clear();
        return null;
      }
      
      return context;
    } catch {
      clear();
      return null;
    }
  }, []);
  
  const clear = useCallback((): void => {
    sessionStorage.removeItem(CONTEXT_KEY);
  }, []);
  
  return { save, restore, clear };
}
```

---

#### `FlowsList.tsx` — Componente Principal

**Responsabilidade:** Renderizar grid de flows, gerenciar paginação, restaurar contexto.

```typescript
export function FlowsList({ config }: { config: AppConfig }) {
  const [page, setPage] = useState(1);
  const pageSize = 12;  // flows por página
  
  const { flows, loading, error, refetch } = useFlows(config);
  const { save, restore } = useFlowsContext();
  
  // Restaurar contexto ao montar
  useEffect(() => {
    const saved = restore();
    if (saved) {
      setPage(saved.currentPage);
      // Scroll restaurado após render
      setTimeout(() => window.scrollTo(0, saved.scrollPosition), 100);
    }
  }, [restore]);
  
  // Salvar contexto antes de navegar
  const handleEditFlow = (flowId: string) => {
    save({
      currentPage: page,
      scrollPosition: window.scrollY,
      timestamp: Date.now()
    });
    window.location.href = `/flows/${flowId}`;
  };
  
  if (loading) {
    return <LoadingState />;
  }
  
  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={refetch}
      />
    );
  }
  
  if (!flows || flows.length === 0) {
    return <EmptyState />;
  }
  
  const totalPages = Math.ceil(flows.length / pageSize);
  const paginatedFlows = flows.slice(
    (page - 1) * pageSize,
    page * pageSize
  );
  
  return (
    <div className="flows-container">
      <h1>Meus Flows</h1>
      
      <div className="flows-grid">
        {paginatedFlows.map(flow => (
          <FlowCard
            key={flow.id}
            flow={flow}
            onEdit={() => handleEditFlow(flow.id)}
          />
        ))}
      </div>
      
      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
```

---

#### `FlowCard.tsx` — Card Individual

```typescript
export function FlowCard({
  flow,
  onEdit
}: {
  flow: Flow;
  onEdit: () => void;
}) {
  const formattedDate = new Intl.DateTimeFormat('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(flow.updated_at));
  
  return (
    <article className="flow-card">
      <header className="flow-card-header">
        <h3 className="flow-name">{flow.name}</h3>
      </header>
      
      <section className="flow-card-body">
        {flow.description && (
          <p className="flow-description">{flow.description}</p>
        )}
        <p className="flow-meta">
          Atualizado em: <time dateTime={flow.updated_at}>{formattedDate}</time>
        </p>
      </section>
      
      <footer className="flow-card-footer">
        <button
          className="btn btn-primary"
          onClick={onEdit}
          aria-label={`Editar flow ${flow.name} no Langflow`}
        >
          Editar no Langflow →
        </button>
      </footer>
    </article>
  );
}
```

---

### 2.3 Session Management Architecture (Feature 2)

**Responsabilidade:** Gerenciar autenticação, session refresh automático, interceptação de 401/403, logout após falhas.

**Localização:**
- `frontend/apps/rockitdown/src/stores/authStore.ts` — Zustand auth state
- `frontend/apps/rockitdown/src/stores/sessionStore.ts` — Zustand session state
- `frontend/apps/rockitdown/src/api/axios-client.ts` — Axios com interceptor
- `frontend/apps/rockitdown/src/hooks/useSessionRefresh.ts` — Proactive refresh

#### Type Contracts (src/types/stores.ts)

Já definidos em GATE 2. Referência:
- **AuthStoreState:** isAuthenticated, userId, email, accessToken, refreshToken, tokenExpiresAt, failedRefreshAttempts, maxFailedRefreshAttempts, actions (setAuthenticated, setTokens, incrementErrorCount, logout)
- **SessionStoreState:** isRefreshing, lastRefreshTimestamp, nextRefreshAt, isValidating, lastValidationAt, refreshIntervalMs, actions (startRefresh, endRefresh, startValidation, endValidation)

#### authStore Implementation

```typescript
// frontend/apps/rockitdown/src/stores/authStore.ts
import { create } from 'zustand';
import { AuthStoreState } from '../types/stores';

export const useAuthStore = create<AuthStoreState>((set) => ({
  // State
  isAuthenticated: false,
  userId: undefined,
  email: undefined,
  accessToken: undefined,
  refreshToken: undefined,
  tokenExpiresAt: undefined,
  isSessionValid: true,
  lastRefreshAt: undefined,
  failedRefreshAttempts: 0,
  maxFailedRefreshAttempts: 3,
  
  // Actions
  setAuthenticated: (isAuth: boolean) => set({ isAuthenticated: isAuth }),
  setTokens: (access: string, refresh: string, expiresAt: number) =>
    set({ accessToken: access, refreshToken: refresh, tokenExpiresAt: expiresAt }),
  setSessionValid: (valid: boolean) => set({ isSessionValid: valid }),
  incrementErrorCount: () => set((state) => ({
    failedRefreshAttempts: state.failedRefreshAttempts + 1
  })),
  resetErrorCount: () => set({ failedRefreshAttempts: 0 }),
  logout: () => set({
    isAuthenticated: false,
    accessToken: undefined,
    refreshToken: undefined,
    failedRefreshAttempts: 0
  }),
  
  // Computed
  getTokenExpiresSoon: () => {
    const state = useAuthStore.getState();
    if (!state.tokenExpiresAt) return false;
    const expiresIn = state.tokenExpiresAt - Date.now();
    return expiresIn < 10 * 60 * 1000; // 10 minutes
  }
}));
```

#### Axios Client with Response Interceptor

```typescript
// frontend/apps/rockitdown/src/api/axios-client.ts
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const axiosClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Include Django session cookie
  timeout: 10000
});

// Response interceptor: handle 401/403, retry with exponential backoff
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    const authStore = useAuthStore.getState();
    
    // 401 Unauthorized: Session expired or invalid
    if (response?.status === 401) {
      authStore.incrementErrorCount();
      
      if (authStore.failedRefreshAttempts >= authStore.maxFailedRefreshAttempts) {
        // Max retries exceeded: logout
        authStore.logout();
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      // Retry with exponential backoff
      const delay = Math.pow(2, authStore.failedRefreshAttempts) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      return axiosClient(config);
    }
    
    // 403 Forbidden: User not in tenant or workspace invalid
    if (response?.status === 403) {
      console.error('Access denied:', response.data);
      return Promise.reject(error);
    }
    
    return Promise.reject(error);
  }
);
```

#### useSessionRefresh Hook

```typescript
// frontend/apps/rockitdown/src/hooks/useSessionRefresh.ts
import { useEffect, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useSessionStore } from '../stores/sessionStore';
import { axiosClient } from '../api/axios-client';
import { AppConfig } from '../types';

export function useSessionRefresh(config: AppConfig) {
  const authStore = useAuthStore();
  const sessionStore = useSessionStore();
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    if (!authStore.isAuthenticated) return;
    
    // Calculate next refresh: 54 minutes from now (90% of 60 min session)
    const nextRefreshAt = Date.now() + (54 * 60 * 1000);
    sessionStore.setNextRefresh(nextRefreshAt);
    
    // Setup proactive refresh timer
    refreshTimerRef.current = setTimeout(async () => {
      sessionStore.startRefresh();
      
      try {
        // Call refresh endpoint (backend provides)
        const response = await axiosClient.post('/session/refresh', {});
        authStore.resetErrorCount();
        sessionStore.endRefresh(true);
      } catch (error) {
        sessionStore.endRefresh(false, String(error));
        authStore.incrementErrorCount();
      }
    }, nextRefreshAt - Date.now());
    
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [authStore.isAuthenticated, authStore.tokenExpiresAt]);
  
  return { isRefreshing: sessionStore.isRefreshing };
}
```

**Flow:**
1. User logs in → authStore.setAuthenticated(true), set tokens
2. ProtectedRoute mounts → useSessionRefresh activates
3. After 54 min → Proactive refresh timer fires
4. If refresh succeeds → Reset error count, schedule next refresh
5. If refresh fails 3x → Logout user, redirect to /login

---

### 2.4 Global Error Handling Strategy (Feature 9)

**Localização:**
- `frontend/apps/rockitdown/src/components/ErrorBoundary.tsx` — Catch React errors
- `frontend/apps/rockitdown/src/components/Toast.tsx` — Toast notifications (shadcn-ui)
- Error recovery in hooks (useFlows, useSessionRefresh, etc.)

**ErrorBoundary:**
```typescript
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // Send to error tracking (Sentry, etc.)
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold">Algo deu errado</h1>
            <p className="text-gray-600">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
            >
              Recarregar página
            </button>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

**Retry Strategy by Error Type:**

| Error Type | HTTP Status | Strategy | User Feedback |
|------------|------------|----------|---|
| Session expired | 401 | Auto-logout after 3 retries (exponential backoff) | Toast: "Sessão expirada. Faça login novamente" |
| Not in tenant | 403 | Deny access, show error | Toast: "Você não tem acesso a este workspace" |
| Workspace not found | 404 | Show setup wizard (Phase 2) | Toast: "Workspace não configurado" |
| Langflow unavailable | 503 | Retry with exponential backoff (max 3) | Toast: "Langflow temporariamente indisponível" |
| Network error | - | Retry with exponential backoff (max 3) | Toast: "Erro de conexão. Tentando novamente..." |
| Unexpected error | 500 | Log to error tracking; show generic error | Toast: "Erro inesperado. Recarregue a página" |

---

## 3. Styling Strategy (Feature 8: Tailwind CSS)

### 3.1 Tailwind CSS Setup

**Instalação:**
```bash
cd frontend/apps/rockitdown
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**tailwind.config.ts:**
```typescript
import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#8b5cf6',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
      }
    },
  },
  plugins: [],
} satisfies Config
```

**src/index.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .flow-card {
    @apply bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow;
  }
  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded;
  }
}
```

**Styling Examples:**
- FlowsList grid: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`
- Sidebar layout: `flex h-screen bg-gray-50`
- Loading spinner: `animate-spin rounded-full h-12 w-12 border-b-2`
- Error state: `bg-red-50 border border-red-200 rounded-lg p-4`

---

---

## 4. Data Flow Diagrams (Fluxo de Dados End-to-End)

### 4.1 Fluxo 1: Carregamento Inicial de Flows

```
Browser                Django (RID)           FastAPI (API)          Langflow
   │                      │                        │                    │
   │  GET /app/flows      │                        │                    │
   ├─────────────────────>│                        │                    │
   │                      │ Check session + tenant │                    │
   │                      │ (LoginRequiredMixin)   │                    │
   │  HTML + app-config   │                        │                    │
   │<─────────────────────┤                        │                    │
   │                      │                        │                    │
   │ React mount FlowsList│                        │                    │
   │ useFlows hook        │                        │                    │
   │ Axios GET /api/v1..  │                        │                    │
   ├────────────────────────────────────────────>  │                    │
   │                      │  GET /api/v1/langflow/ │                    │
   │                      │      flows/list        │                    │
   │                      ├────────────────────>   │                    │
   │                      │                        │ Validate session   │
   │                      │                        │ + tenant + member  │
   │                      │                        │ Fetch creds        │
   │                      │                        │ GET /api/v1/       │
   │                      │                        │ projects/{id}/flows│
   │                      │                        ├───────────────────>│
   │                      │                        │ [Flow List JSON]   │
   │                      │                        │<───────────────────┤
   │                      │ Transform & validate   │                    │
   │  JSON 200 + flows    │<────────────────────┤  │
   │<─────────────────────────────────────────────┤                    │
   │                      │                        │                    │
   │ authStore.resetError │                        │                    │
   │ Render grid          │                        │                    │
   │ useFlowsContext.rest │                        │                    │
```

### 4.2 Fluxo 2: Navegação para Langflow Editor

```
Browser                RID Frontend             Traefik            Langflow
   │                      │                        │                    │
   │ User click "Edit"    │                        │                    │
   │ handleEditFlow()     │                        │                    │
   │ 1. save to storage   │                        │                    │
   │ 2. window.location=  │                        │                    │
   │    /flows/{id}       │                        │                    │
   ├──────────────────────────────────────────────>│                    │
   │                      │                        │ forwardAuth:       │
   │                      │                        │ GET /internal/     │
   │                      │                        │ auth-check/        │
   │                      │                        ├───────────────────>│
   │                      │                        │ Validate session   │
   │                      │                        │ + tenant           │
   │                      │                        │ 200 OK             │
   │                      │                        │<───────────────────┤
   │                      │                        │                    │
   │                      │ Forward to Langflow    │                    │
   │                      │<─────────────────────────────────────────>│
   │                      │ Render editor         │                    │
   │                      │ (auto-login cookie)   │                    │
   │<─────────────────────────────────────────────────────────────────┤
```

### 4.3 Fluxo 3: Retorno (Back Button Recovery)

```
Browser                RID Frontend            sessionStorage
   │                      │                        │
   │ User click back      │                        │
   ├─────────────────────>│                        │
   │                      │ Navigate to           │
   │                      │ /app/flows             │
   │                      │                        │
   │ React remount        │                        │
   │ FlowsList            │                        │
   │ useFlowsContext      │                        │
   │ .restore()           │                        │
   │                      │ read('flows_context')  │
   │                      │<───────────────────────┤
   │                      │ {page, scroll, ts}     │
   │                      │ Validate TTL (30m)     │
   │                      │ setPage(2)             │
   │                      │ setTimeout(scroll)     │
   │                      │ clear()                │
   │                      ├───────────────────────>│
   │ Render page 2        │                        │
   │ + scroll restored    │                        │
   │<─────────────────────┤                        │
```

---

## 5. Testing Strategy (Features 7a and 7b)

### 5.1 Feature 7a: Unit + Component Tests (parallelizable with Feature 4)

**Scope:** Isolated tests using mocks. No real backend calls. Runs in parallel with Feature 4 implementation.

#### 5.1.1 useFlowsContext Hook Tests

**Arquivo:** `frontend/apps/rockitdown/src/hooks/__tests__/useFlowsContext.test.ts`

**FASE RED:** Testes falhando antes de implementação.

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFlowsContext } from '../useFlowsContext';

describe('useFlowsContext', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('should save context to sessionStorage', () => {
    const { result } = renderHook(() => useFlowsContext());
    
    const context = {
      currentPage: 2,
      scrollPosition: 500,
      timestamp: Date.now()
    };
    
    act(() => {
      result.current.save(context);
    });
    
    const saved = JSON.parse(sessionStorage.getItem('flows_list_context') || '{}');
    expect(saved.currentPage).toBe(2);
    expect(saved.scrollPosition).toBe(500);
  });

  it('should restore valid context', () => {
    const now = Date.now();
    sessionStorage.setItem('flows_list_context', JSON.stringify({
      currentPage: 3,
      scrollPosition: 1000,
      timestamp: now
    }));
    
    const { result } = renderHook(() => useFlowsContext());
    const restored = result.current.restore();
    
    expect(restored?.currentPage).toBe(3);
    expect(restored?.scrollPosition).toBe(1000);
  });

  it('should return null for expired context (>30 min)', () => {
    const thirtyMinutesAgo = Date.now() - 31 * 60 * 1000;
    sessionStorage.setItem('flows_list_context', JSON.stringify({
      currentPage: 1,
      scrollPosition: 0,
      timestamp: thirtyMinutesAgo
    }));
    
    const { result } = renderHook(() => useFlowsContext());
    const restored = result.current.restore();
    
    expect(restored).toBeNull();
  });

  it('should clear context from sessionStorage', () => {
    sessionStorage.setItem('flows_list_context', JSON.stringify({
      currentPage: 1,
      scrollPosition: 0,
      timestamp: Date.now()
    }));
    
    const { result } = renderHook(() => useFlowsContext());
    act(() => {
      result.current.clear();
    });
    
    expect(sessionStorage.getItem('flows_list_context')).toBeNull();
  });
});
```

**FASE GREEN:** Implementar `useFlowsContext.ts` até testes passarem.

**FASE REFACTOR:** Otimizar performance, adicionar edge cases.

---

#### 5.1.2 useFlows Hook Tests

**Arquivo:** `frontend/apps/rockitdown/src/hooks/__tests__/useFlows.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useFlows } from '../useFlows';

const mockConfig: AppConfig = {
  tenant: { schema_name: 'test', user_email: 'user@test.com', user_id: '1' },
  api: {
    base_url: '/api/v1',
    langflow_auto_login_url: '/api/v1/langflow/auth/auto-login',
    langflow_base_url: 'http://localhost:7860'
  },
  csrf_token: 'test-token'
};

describe('useFlows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch flows on mount', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        flows: [
          {
            id: 'flow-1',
            name: 'Test Flow',
            description: 'Test',
            updated_at: '2026-04-11T00:00:00Z',
            created_at: '2026-04-10T00:00:00Z'
          }
        ],
        workspace_id: 'ws-1',
        total_count: 1
      })
    });
    
    const { result } = renderHook(() => useFlows(mockConfig));
    
    expect(result.current.loading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    expect(result.current.flows).toHaveLength(1);
    expect(result.current.flows?.[0].name).toBe('Test Flow');
    expect(result.current.error).toBeNull();
  });

  it('should handle 401 error', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized'
    });
    
    const { result } = renderHook(() => useFlows(mockConfig));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    expect(result.current.error).toContain('Sessão expirada');
    expect(result.current.flows).toBeNull();
  });

  it('should handle 503 error', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable'
    });
    
    const { result } = renderHook(() => useFlows(mockConfig));
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    expect(result.current.error).toContain('temporariamente indisponível');
  });

  it('should abort fetch on unmount', async () => {
    const abortSpy = vi.spyOn(AbortController.prototype, 'abort');
    
    global.fetch = vi.fn(() => new Promise(() => {}));  // Never resolves
    
    const { unmount } = renderHook(() => useFlows(mockConfig));
    
    unmount();
    
    expect(abortSpy).toHaveBeenCalled();
  });
});
```

---

#### 5.1.3 FlowsList Component Tests

**Arquivo:** `frontend/apps/rockitdown/src/components/__tests__/FlowsList.test.tsx`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FlowsList } from '../FlowsList';

const mockConfig: AppConfig = { /* ... */ };

describe('FlowsList', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it('should render loading state', () => {
    global.fetch = vi.fn(() => new Promise(() => {}));
    
    render(<FlowsList config={mockConfig} />);
    
    expect(screen.getByText(/carregando/i)).toBeInTheDocument();
  });

  it('should render flows grid after loading', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        flows: [
          {
            id: '1',
            name: 'Flow 1',
            description: 'Test',
            updated_at: '2026-04-11T00:00:00Z',
            created_at: '2026-04-10T00:00:00Z'
          }
        ],
        workspace_id: 'ws-1',
        total_count: 1
      })
    });
    
    render(<FlowsList config={mockConfig} />);
    
    await waitFor(() => {
      expect(screen.getByText('Flow 1')).toBeInTheDocument();
    });
  });

  it('should save context before navigating to Langflow', async () => {
    const setItemSpy = vi.spyOn(sessionStorage, 'setItem');
    const originalLocation = window.location;
    delete window.location;
    window.location = { href: '' } as any;
    
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        flows: [
          {
            id: '1',
            name: 'Flow 1',
            description: 'Test',
            updated_at: '2026-04-11T00:00:00Z',
            created_at: '2026-04-10T00:00:00Z'
          }
        ],
        workspace_id: 'ws-1',
        total_count: 1
      })
    });
    
    render(<FlowsList config={mockConfig} />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByRole('button', { name: /editar/i }));
    });
    
    expect(setItemSpy).toHaveBeenCalledWith(
      'flows_list_context',
      expect.stringContaining('currentPage')
    );
    
    window.location = originalLocation;
  });

  it('should render empty state when no flows', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        flows: [],
        workspace_id: 'ws-1',
        total_count: 0
      })
    });
    
    render(<FlowsList config={mockConfig} />);
    
    await waitFor(() => {
      expect(screen.getByText(/nenhum flow encontrado/i)).toBeInTheDocument();
    });
  });
});
```

---

### 5.2 Feature 7b: Integration + E2E Tests (after Feature 6 complete)

**Scope:** Real backend endpoint + Langflow mock + full user flow. Runs after Feature 6 is complete.

#### 5.2.1 Backend Endpoint Integration Test

**Arquivo:** `backend/tests/test_langflow_flows_list.py`

```python
import pytest
from django.test import AsyncClient
from rest_framework import status
from unittest.mock import patch, AsyncMock

@pytest.mark.django_db(transaction=True)
class TestFlowsListEndpoint:
    
    async def test_list_flows_authenticated_user(self, customer, authenticated_user):
        """Usuário autenticado deve ver flows do seu workspace."""
        # Setup
        customer.langflow_workspace_id = 'test-ws-id'
        customer.langflow_service_api_key = 'test-api-key'
        await sync_to_async(customer.save)()
        
        # Mock Langflow API
        with patch('api.routers.langflow_flows.httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                'data': [
                    {
                        'id': 'flow-1',
                        'name': 'Customer Bot',
                        'description': 'Support bot',
                        'updated_at': '2026-04-11T00:00:00Z',
                        'created_at': '2026-04-10T00:00:00Z'
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            client = AsyncClient()
            response = await client.get(
                '/api/v1/langflow/flows/list',
                headers={'X-Tenant-Id': str(customer.public_tenant_id)},
                HTTP_COOKIE=f'sessionid={authenticated_user.session_key}'
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['flows']) == 1
        assert data['flows'][0]['name'] == 'Customer Bot'
        assert data['workspace_id'] == 'test-ws-id'
    
    async def test_list_flows_unauthenticated(self):
        """Usuário não autenticado deve receber 401."""
        client = AsyncClient()
        response = await client.get('/api/v1/langflow/flows/list')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_list_flows_workspace_not_provisioned(self, customer, authenticated_user):
        """Cliente sem workspace provisionado deve receber 503."""
        customer.langflow_workspace_id = None
        await sync_to_async(customer.save)()
        
        client = AsyncClient()
        response = await client.get(
            '/api/v1/langflow/flows/list',
            headers={'X-Tenant-Id': str(customer.public_tenant_id)},
            HTTP_COOKIE=f'sessionid={authenticated_user.session_key}'
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
```

---

## 6. Type Contracts Reference (src/types/stores.ts)

**File:** `/home/RID/frontend/apps/rockitdown/src/types/stores.ts` (already created, GATE 2 P0 blocker)

**AuthStoreState** (Feature 2):
- `isAuthenticated`: boolean
- `userId`, `email`: string | undefined
- `accessToken`, `refreshToken`: string | undefined
- `tokenExpiresAt`: number (Unix timestamp, ms)
- `failedRefreshAttempts`: number (0-3, auto-logout after max)
- `setAuthenticated()`, `setTokens()`, `incrementErrorCount()`, `logout()`: actions

**SessionStoreState** (Feature 2):
- `isRefreshing`: boolean
- `lastRefreshTimestamp`: number
- `nextRefreshAt`: number (54 min from now)
- `refreshIntervalMs`: number (default: 54 * 60 * 1000)
- `startRefresh()`, `endRefresh()`, `setNextRefresh()`: actions

**FlowStoreState** (Feature 4):
- `flows[]`: Array<{id, name, description, created_at, updated_at}>
- `currentPage`, `pageSize`, `totalCount`: numbers
- `isLoading`, `isInitialized`: boolean
- `error`: {code, message, timestamp} | undefined
- `setFlows()`, `setLoading()`, `setError()`: actions

**ContextStoreState** (Feature 6):
- `flowsListContext`: {page, scroll, timestamp} | undefined
- `contextExpiryMs`: number (default: 30 * 60 * 1000)
- `saveContext()`, `restoreContext()`, `clearContext()`: actions

---

## 7. Checklist de Conformidade com ADRs

| ADR | Requerimento | Implementação | Status |
|-----|--------------|----------------|--------|
| **ADR-001** | Async context: `sync_to_async(thread_sensitive=True)` | Endpoint usa `sync_to_async` para Customer.objects.get | ✅ |
| **ADR-002** | Separação SHARED_APPS (auth) vs TENANT_APPS | FlowsList acessa Customer (public); Langflow API (external) | ✅ |
| **ADR-003** | ASGI hybrid: /api/* → FastAPI | Endpoint em `backend/api/routers/langflow_flows.py` | ✅ |
| **ADR-005** | TenantAwareBackend + Django session | `get_current_user` dependency valida sessão | ✅ |
| **ADR-009** | Langflow: workspace per customer, service API key | Usa Customer.langflow_workspace_id + langflow_service_api_key | ✅ |
| **ADR-012** | Traefik auth gate para `/flows/*` | Traefik protege `/flows/*` via forwardAuth | ✅ |

---

## 8. Critical Path & Execution Order

**Dependency Graph (Features 1-9):**

```
F1 (Backend Endpoint)
  ↓
F2 (Session Management)
  ↓
F3 (React Router)
  ↓
F4 (FlowsList) ← Can parallelize with F7a
  ↓ & ↓
F5 (Navigation) F7a (Unit/Component Tests)
  ↓
F6 (Context Persistence)
  ↓
F7b (Integration/E2E Tests)
  ↓
F8 (Tailwind) & F9 (Error Handling) — can run in parallel
```

**Timeline with 2 Engineers:**

| Phase | Feature | Engineer | Duration | Critical Path |
|-------|---------|----------|----------|---|
| **P1** | F1: Backend Endpoint | Backend | 4-6h | Blocking all |
| **P1** | F2: Session Management | Frontend | 3-4h | Blocking F3, F4 |
| **P1** | F3: React Router | Frontend | 2-3h | Blocking F4 |
| **P2** | F4: FlowsList Component | Frontend | 4-5h | ✅ Parallel |
| **P2** | F7a: Unit/Component Tests | Frontend QA | 4-5h | ✅ Parallel with F4 |
| **P2** | F5: Navigation | Frontend | 1-2h | After F4 |
| **P3** | F6: Context Persistence | Frontend | 2-3h | After F5 |
| **P3** | F7b: Integration/E2E Tests | Backend/Frontend QA | 4-5h | After F6 |
| **P4** | F8: Tailwind Styling | Frontend | 2-3h | ✅ Parallel |
| **P4** | F9: Error Handling | Frontend | 2-3h | ✅ Parallel |

**Estimated Total:** 28-36h of individual work; 15-22h wall-clock with 2 engineers

**Critical Path (minimum):** F1 → F2 → F3 → F4 + F7a → F5 → F6 → F7b = 24-30h
**Parallel Optimization:** F7a runs during F4; F8+F9 run during F7b

---

## 9. Considerações de Segurança

### 9.1 Matriz de Ameaças

| Ameaça | Mitigação | Status |
|--------|-----------|--------|
| **XSS via flow.name** | React escapa HTML automaticamente | ✅ Safe by default |
| **CSRF** | Django CSRF token em cada request | ✅ Validado em middleware |
| **Cross-tenant access** | TenantMembership + workspace_id validation | ✅ Backend enforced |
| **Session fixation** | sessionStorage é per-browser | ✅ Isolated |
| **Token exposure** | Nenhum token em URLs; httpOnly cookies | ✅ By design |
| **Langflow creds leak** | Server-side only; nunca expostas ao cliente | ✅ Secure pattern |

---

## 10. Próximas Etapas

**GATE 3 Completo:**
✅ Especificação técnica do endpoint
✅ Arquitetura de componentes
✅ Fluxo de dados
✅ Estratégia de testes
✅ Conformidade com ADRs

**Próximo:** GATE 4 (Detalhamento de Tarefas)
- Quebra em T-001, T-002, ... T-009
- Dependências e ordem de execução
- Estimativa de horas por tarefa
- Critério de aceitação por tarefa
