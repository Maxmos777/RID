---
title: Frontend Libs Alignment — RID MVP vs Langflow
date: 2026-04-11
status: draft
---

# Frontend Libs Alignment: Convergência com Langflow

## Objetivo

Documentar as bibliotecas e padrões de código que o MVP de Frontend Flows deve usar para **convergir com Langflow** em vez de usar libs diferentes.

---

## 1. Core Dependencies (MUDAR)

### ❌ ANTES (MVP Initial — Não usar mais)

| Lib | Versão | Problema |
|-----|--------|----------|
| `fetch` nativo | builtin | Sem interceptadores; error handling manual |
| `React Context` | builtin | Para tudo; não escalável |
| `localStorage` só | builtin | Sem HttpOnly cookies; inseguro |
| `Tailwind CSS` inline | 3.4.4 | Sem sistema de componentes |
| `React Router` v7 | 7.x | Difere de Langflow (v6.23.1) |

### ✅ DEPOIS (MVP Alinhado com Langflow)

| Lib | Versão | Justificativa | Uso |
|-----|--------|--------------|-----|
| **Axios** | 1.7.4 | HTTP client com interceptadores nativas | Todas as chamadas API |
| **Zustand** | 4.5.2 | State management descentralizado (authStore, sessionStore) | Auth + UI state |
| **React Context** | builtin | Apenas para AuthProvider (wrapper) | Provider inicial |
| **HttpOnly Cookies** | HTTP-only | Cookies gerenciados pelo backend | Refresh token (seguro) |
| **Tailwind CSS** | 3.4.4 | Utility-first styling | Base de styling |
| **shadcn-ui** | 0.9.4 | Componentes customizáveis (Button, Card, Modal) | Componentes comuns |
| **React Router** | 6.23.1 | Alinhado com Langflow | Roteamento + protected routes |
| **TypeScript** | 5.4.5 | Type safety | Todos os novos arquivos |

---

## 2. Estrutura de Arquivos (Novo Pattern)

### 2.1 Organização

```
frontend/apps/rockitdown/src/
├── stores/                          # Zustand stores
│   ├── authStore.ts                 # Auth state (isAuthenticated, accessToken, userData)
│   ├── sessionStore.ts              # Session state (sessionExpired, errorCount)
│   └── flowStore.ts                 # Flow state (flowsData, filters, pagination)
│
├── api/                             # HTTP client + endpoints
│   ├── axios-client.ts              # Axios instance com interceptadores
│   ├── auth.ts                      # Auth endpoints (login, refresh, logout)
│   └── flows.ts                     # Flows endpoints (list, get, etc)
│
├── hooks/                           # React hooks (padrão Langflow)
│   ├── useSessionRefresh.ts         # Proactive token refresh
│   ├── useFlows.ts                  # Fetch flows (wrapper de Axios)
│   ├── useAuth.ts                   # Auth state + actions
│   └── __tests__/                   # Testes de hooks
│
├── components/                      # React components
│   ├── FlowsList.tsx                # Listagem de flows
│   ├── FlowCard.tsx                 # Card de flow
│   ├── SessionExpiryModal.tsx        # Modal de session expirada
│   ├── ProtectedRoute.tsx            # Route guard
│   └── __tests__/                   # Testes de componentes
│
├── pages/                           # Páginas/rotas
│   ├── FlowsPage.tsx                # Página de flows
│   ├── LoginPage.tsx                # Página de login
│   └── AppInitPage.tsx              # Init + session validation
│
├── types/                           # TypeScript types
│   ├── auth.ts
│   ├── flows.ts
│   └── api.ts
│
├── utils/                           # Utilidades
│   ├── cookie-manager.ts            # Helper para cookies
│   └── env.ts                       # Env vars
│
├── contexts/                        # React Context (mínimo)
│   └── AuthProvider.tsx             # Context provider de auth
│
├── App.tsx                          # Root component
├── main.tsx                         # Entry point
└── index.css                        # Global styles
```

---

## 3. Patterns de Código (Langflow → RID)

### 3.1 Auth Store (Zustand)

**Langflow Pattern** (em `/src/stores/authStore.ts`):

```typescript
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface AuthStoreState {
  isAuthenticated: boolean;
  accessToken: string | null;
  userData: User | null;
  autoLogin: boolean | null;
  authErrorCount: number;
  
  // Actions
  setIsAuthenticated: (auth: boolean) => void;
  setAccessToken: (token: string) => void;
  setUserData: (user: User) => void;
  logout: () => void;
  incrementErrorCount: () => void;
  resetErrorCount: () => void;
}

export const useAuthStore = create<AuthStoreState>(
  subscribeWithSelector((set) => ({
    isAuthenticated: false,
    accessToken: null,
    userData: null,
    autoLogin: null,
    authErrorCount: 0,
    
    setIsAuthenticated: (auth) => set({ isAuthenticated: auth }),
    setAccessToken: (token) => set({ accessToken: token }),
    setUserData: (user) => set({ userData: user }),
    logout: () => set({
      isAuthenticated: false,
      accessToken: null,
      userData: null,
      authErrorCount: 0
    }),
    incrementErrorCount: () => set((state) => ({
      authErrorCount: state.authErrorCount + 1
    })),
    resetErrorCount: () => set({ authErrorCount: 0 })
  }))
);
```

**Uso em Componentes**:

```typescript
function LoginForm() {
  const setIsAuthenticated = useAuthStore((s) => s.setIsAuthenticated);
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  
  // ou shorthand
  const { setIsAuthenticated, setAccessToken } = useAuthStore();
  
  return (
    <form onSubmit={async (e) => {
      e.preventDefault();
      const response = await apiClient.post('/login', { email, password });
      setAccessToken(response.data.access_token);
      setIsAuthenticated(true);
    }}>
      {/* form fields */}
    </form>
  );
}
```

---

### 3.2 Axios Client com Interceptadores

**Langflow Pattern** (em `/src/api/axios-client.ts`):

```typescript
import axios, { AxiosError, AxiosResponse } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // ← CRITICAL: envia HttpOnly cookies
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Response Interceptor (detecção de session expiry)
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Success: reset error count
    useAuthStore.getState().resetErrorCount();
    return response;
  },
  async (error: AxiosError) => {
    const isAuthError = 
      error?.response?.status === 401 || 
      error?.response?.status === 403;
    
    const authStore = useAuthStore.getState();
    const isAutoLogin = authStore.autoLogin;
    
    if (isAuthError && !isAutoLogin) {
      authStore.incrementErrorCount();
      
      // Max 3 tentativas
      if (authStore.authErrorCount >= 3) {
        authStore.logout();
        window.location.href = '/login?redirect=' + window.location.pathname;
        return Promise.reject(error);
      }
      
      // Tenta renovar token
      try {
        const response = await axios.post(
          `${API_BASE_URL}/langflow/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        const newToken = response.data?.access_token;
        if (newToken) {
          authStore.setAccessToken(newToken);
          authStore.resetErrorCount();
          
          // Retry original request
          if (error.config) {
            return apiClient.request(error.config);
          }
        }
      } catch (refreshError) {
        authStore.logout();
        window.location.href = '/login?redirect=' + window.location.pathname;
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

### 3.3 Hook para Session Refresh (Proativo)

**Langflow Pattern** (em `/src/hooks/useSessionRefresh.ts`):

```typescript
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/api/axios-client';

const ACCESS_TOKEN_EXPIRE_SECONDS = 
  Number(import.meta.env.VITE_ACCESS_TOKEN_EXPIRE_SECONDS || 3600);

export function useSessionRefresh() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const autoLogin = useAuthStore((s) => s.autoLogin);
  
  useEffect(() => {
    if (!isAuthenticated || autoLogin) {
      return;  // Skip se not auth ou autoLogin
    }
    
    // Refresh 90% antes de expirar
    const refreshInterval = ACCESS_TOKEN_EXPIRE_SECONDS * 0.9 * 1000;
    
    const interval = setInterval(async () => {
      try {
        const response = await apiClient.post('/langflow/auth/refresh');
        const newToken = response.data?.access_token;
        if (newToken) {
          useAuthStore.getState().setAccessToken(newToken);
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        // Interceptor já trata logout
      }
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [isAuthenticated, autoLogin]);
}
```

**Uso em App.tsx**:

```typescript
function App() {
  useSessionRefresh();  // Ativa proactive refresh
  
  return <Routes>{/* rotas */}</Routes>;
}
```

---

### 3.4 Hook para Fetch (Wrapper de Axios)

**RID Pattern** (em `/src/hooks/useFlows.ts`):

```typescript
import { useEffect, useState } from 'react';
import { apiClient } from '@/api/axios-client';

interface FlowsResponse {
  flows: Flow[];
  workspace_id: string;
  total_count: number;
}

export function useFlows() {
  const [flows, setFlows] = useState<Flow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchFlows = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiClient.get<FlowsResponse>(
          '/langflow/flows/list'
        );
        setFlows(response.data.flows);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Erro ao carregar flows');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchFlows();
  }, []);
  
  return { flows, loading, error };
}
```

---

### 3.5 Protected Route Guard

**Langflow Pattern** (em `/src/components/ProtectedRoute.tsx`):

```typescript
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const autoLogin = useAuthStore((s) => s.autoLogin);
  
  // Redireciona se não autenticado
  if (!isAuthenticated && autoLogin !== true) {
    return <Navigate to="/login" replace />;
  }
  
  return <Outlet />;
}

// Em Router config:
export const routes = [
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      { path: 'flows', element: <FlowsPage /> },
      { path: 'app', element: <AppPage /> }
    ]
  },
  {
    path: '/login',
    element: <LoginPage />
  }
];
```

---

### 3.6 Tipos TypeScript (Langflow Style)

**Em `/src/types/auth.ts`**:

```typescript
export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user?: User;
}

export interface SessionResponse {
  authenticated: boolean;
  user?: User;
  store_api_key?: string;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token?: string;
}
```

**Em `/src/types/flows.ts`**:

```typescript
export interface Flow {
  id: string;
  name: string;
  description?: string;
  updated_at: string;
  created_at: string;
}

export interface FlowsListResponse {
  flows: Flow[];
  workspace_id: string;
  total_count: number;
}
```

---

## 4. Testes (Padrão Langflow)

### 4.1 Testes de Hooks (Vitest)

**Em `/src/hooks/__tests__/useSessionRefresh.test.ts`**:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useSessionRefresh } from '../useSessionRefresh';
import { useAuthStore } from '@/stores/authStore';
import * as api from '@/api/axios-client';

describe('useSessionRefresh', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      isAuthenticated: true,
      accessToken: 'test-token',
      autoLogin: false
    });
  });

  it('should refresh token before expiration', async () => {
    const mockPost = vi.spyOn(api.apiClient, 'post');
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'new-token' }
    });
    
    vi.useFakeTimers();
    renderHook(() => useSessionRefresh());
    
    // Fast-forward 54 min
    vi.advanceTimersByTime(54 * 60 * 1000);
    
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/langflow/auth/refresh');
    });
    
    const newToken = useAuthStore.getState().accessToken;
    expect(newToken).toBe('new-token');
    
    vi.useRealTimers();
  });

  it('should not refresh if autoLogin is true', () => {
    useAuthStore.setState({ autoLogin: true });
    const mockPost = vi.spyOn(api.apiClient, 'post');
    
    renderHook(() => useSessionRefresh());
    
    expect(mockPost).not.toHaveBeenCalled();
  });
});
```

### 4.2 Testes de Store (Zustand)

**Em `/src/stores/__tests__/authStore.test.ts`**:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      isAuthenticated: false,
      accessToken: null,
      userData: null,
      authErrorCount: 0
    });
  });

  it('should set authentication state', () => {
    useAuthStore.getState().setIsAuthenticated(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('should increment error count', () => {
    useAuthStore.getState().incrementErrorCount();
    useAuthStore.getState().incrementErrorCount();
    
    expect(useAuthStore.getState().authErrorCount).toBe(2);
  });

  it('should logout and reset state', () => {
    useAuthStore.getState().setIsAuthenticated(true);
    useAuthStore.getState().setAccessToken('token');
    useAuthStore.getState().logout();
    
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().authErrorCount).toBe(0);
  });
});
```

### 4.3 Testes de Interceptor (Axios)

**Em `/src/api/__tests__/axios-client.test.ts`**:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from '../axios-client';
import { useAuthStore } from '@/stores/authStore';

describe('apiClient interceptor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ isAuthenticated: true, authErrorCount: 0 });
  });

  it('should increment error count on 401', async () => {
    const error = new Error('401 Unauthorized');
    (error as any).response = { status: 401, data: {} };
    
    // Mock interceptor
    // (Este teste requer setup mais complexo; veja pattern em Langflow)
  });
});
```

---

## 5. Mudanças Required (Package.json)

### 5.1 Adicionar

```json
{
  "dependencies": {
    "axios": "^1.7.4",
    "zustand": "^4.5.2",
    "react-router-dom": "^6.23.1",
    "tailwindcss": "^3.4.4",
    "shadcn-ui": "^0.9.4"
  },
  "devDependencies": {
    "@testing-library/react": "^15.x",
    "vitest": "^2.x",
    "typescript": "^5.4.5"
  }
}
```

### 5.2 Remover

- ❌ `react-router-dom@^7.x` (atualizar para 6.23.1)
- ❌ Qualquer alternativa a Zustand (Redux, MobX, etc)
- ❌ fetch wrappers custom

---

## 6. Environment Variables

### 6.1 `.env.example`

```env
# API
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Auth
VITE_ACCESS_TOKEN_EXPIRE_SECONDS=3600
VITE_AUTO_LOGIN=false

# Debug
VITE_DEBUG=false
```

---

## 7. Migração de Código Anterior

### 7.1 O que MUDAR

| Arquivo/Pattern | De | Para | Arquivo Novo |
|-----------------|----|----|----------|
| useFlows hook | `fetch` | `apiClient.get()` | `src/hooks/useFlows.ts` |
| useFlowsContext | sessionStorage | Zustand `sessionStore` | `src/stores/sessionStore.ts` |
| App.tsx routing | React Router v7 | v6.23.1 | Refactor config |
| Auth state | Context + useState | Zustand `authStore` | `src/stores/authStore.ts` |
| API calls | Axios nativo | `apiClient` com interceptor | `src/api/axios-client.ts` |
| Types | Inline em componentes | Arquivos em `/src/types/` | `src/types/*.ts` |
| Tests | Padrão anterior | Vitest + @testing-library | `__tests__/` diretórios |

### 7.2 Fase de Migração

1. **GATE 4 (Implementation)**: Usar NOVOS patterns (Zustand, Axios, etc)
2. **Não refatorar código anterior** até Phase 2
3. **Novos componentes** = novo padrão desde o início

---

## 8. Checklist de Implementação (MVP)

### Backend Aligned
- [ ] Endpoint `/login` retorna `{ access_token, token_type }`
- [ ] Endpoint `/refresh` retorna novo `access_token`
- [ ] HttpOnly `refresh_token` cookie em resposta
- [ ] Status 401/403 para erros auth
- [ ] `GET /session` para validação na init

### Frontend Stack
- [ ] `npm install axios@1.7.4 zustand@4.5.2`
- [ ] Criar `authStore.ts` com Zustand
- [ ] Criar `axios-client.ts` com interceptadores
- [ ] Criar `useSessionRefresh.ts` hook
- [ ] Criar `ProtectedRoute.tsx` guard
- [ ] Refatorar `useFlows.ts` para usar Axios
- [ ] TypeScript types em `/src/types/`
- [ ] Testes para hooks + store + interceptor

### Verificação Final
- [ ] Nenhum `fetch` nativo em novos arquivos (use Axios)
- [ ] Nenhum Context para state global (use Zustand)
- [ ] Todos os tipos em `/src/types/`
- [ ] Testes com Vitest + @testing-library
- [ ] Package.json atualizado

---

## 9. Referências

- **Langflow Frontend Source**: https://github.com/langflow-ai/langflow/tree/main/src/frontend
- **Zustand Docs**: https://github.com/pmndrs/zustand
- **Axios Docs**: https://axios-http.com/
- **React Router v6**: https://reactrouter.com/
- **Vitest**: https://vitest.dev/

---

**Documento pronto para GATE 4 (Implementation Planning).**
