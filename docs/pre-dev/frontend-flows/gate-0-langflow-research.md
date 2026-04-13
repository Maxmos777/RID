---
feature: frontend-flows
gate: 0
type: research-spike
date: 2026-04-11
title: Spike Research — Langflow Frontend Architecture & Session Management
---

# SPIKE RESEARCH: Langflow Frontend Architecture & Session Management

## Objetivo

Entender como Langflow implementa autenticação, session management, e detecção de expiry no frontend, além de identificar as libs e padrões para convergência com nosso MVP.

**Fonte**: Análise do repositório oficial https://github.com/langflow-ai/langflow (v1.8.4)

---

## 1. Frontend Technology Stack (Langflow v1.8.4)

### 1.1 Core Stack

| Tecnologia | Versão | Propósito | Status |
|------------|--------|----------|--------|
| **React** | 19.2.1 | Framework principal | ✅ Usar no MVP |
| **TypeScript** | 5.4.5 | Type safety | ✅ Usar no MVP |
| **Vite** | 7.3.1 | Build tool | ✅ Já em uso |
| **Node.js** | ≥20.19.0 | Runtime | ✅ Verificar versão |

### 1.2 State Management

| Lib | Versão | Uso | Impacto |
|-----|--------|-----|--------|
| **Zustand** | 4.5.2 | State management descentralizado | ⭐ PRINCIPAL — Use no MVP |
| **React Context** | builtin | Auth context wrapper | ✅ Use com Zustand |
| **React Query** | 5.49.2 | Data fetching + caching | ✅ Considerar para Phase 2 |

**Pattern Langflow**: 
- Zustand para stores isoladas (authStore, flowStore, sessionManagerStore)
- Context apenas para autenticação (wrapping)
- React Query para dados remotos (optional)

**Recomendação MVP**: **Implementar Zustand desde o início** para alinhamento com Langflow.

### 1.3 HTTP Client & Networking

| Lib | Versão | Uso |
|-----|--------|-----|
| **Axios** | 1.7.4 | HTTP client principal |
| **fetch-intercept** | 2.4.0 | Interceptadores de Fetch |
| **Credentials: include** | - | Envio automático de HttpOnly cookies |

**Pattern Langflow**:
```typescript
const api = axios.create({
  baseURL: baseURL,
  withCredentials: true  // ← CRITICAL para cookies
});

// Interceptadores para erro 401/403
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 || 403) {
      // Tenta refresh token
      await tryToRenewAccessToken();
    }
  }
);
```

**Recomendação MVP**: **Use Axios com interceptadores** em vez de fetch nativo.

### 1.4 UI & Styling

| Lib | Versão | Uso | Para MVP |
|-----|--------|-----|----------|
| **Chakra UI** | latest | Componentes base | ⚠️ Overkill para MVP |
| **Radix UI** | latest | Primitivos acessíveis | ⚠️ Overkill para MVP |
| **Tailwind CSS** | 3.4.4 | Utility-first | ✅ USE |
| **shadcn-ui** | 0.9.4 | Componentes customizáveis | ✅ Use seletivamente |
| **Framer Motion** | latest | Animações | ⚠️ Phase 2 |

**Recomendação MVP**: **Tailwind CSS + shadcn-ui para componentes comuns** (button, card, modal).

### 1.5 Roteamento

| Lib | Versão |
|-----|--------|
| **React Router DOM** | 6.23.1 |

**Pattern Langflow**:
```typescript
// Protected routes com guard
<ProtectedRoute>
  <Outlet />
</ProtectedRoute>

// Login-protected (bloqueia se já logado)
<ProtectedLoginRoute>
  <Login />
</ProtectedLoginRoute>
```

**Recomendação MVP**: **React Router v6** com lazy loading de páginas.

---

## 2. Autenticação & Session Management (RESPOSTA A Q3)

### 2.1 Detecção de Session Expiry em Langflow

**Como Langflow detecta quando a sessão expirou:**

#### Mecanismo 1: Proactive Token Refresh (Preventivo)

```typescript
// ProtectedRoute component (authGuard/index.tsx)
const accessTokenExpirationSeconds = 
  Number(getEnvVar("ACCESS_TOKEN_EXPIRE_SECONDS", 3600)) * 0.9;  // 90% do tempo

if (!autoLogin && isAuthenticated) {
  const timer = setInterval(() => {
    mutateRefresh();  // Chama POST /refresh antes de expirar
  }, accessTokenExpirationSeconds * 1000);
  
  return () => clearInterval(timer);
}
```

**Padrão**: Refresh automático **antes** da expiração (não espera expirar).

#### Mecanismo 2: Response Interceptor (Reativo)

```typescript
// controllers/API/api.tsx (linhas 65-99)
const interceptor = api.interceptors.response.use(
  (response) => {
    setHealthCheckTimeout(null);
    return response;
  },
  async (error: AxiosError) => {
    const isAuthenticationError = 
      error?.response?.status === 403 || 
      error?.response?.status === 401;  // ← Detecta aqui
    
    const shouldRetryRefresh = 
      (isAuthenticationError && !IS_AUTO_LOGIN) ||
      (isAuthenticationError && !autoLogin && autoLogin !== undefined);
    
    if (shouldRetryRefresh) {
      const stillRefresh = checkErrorCount();  // Max 3 tentativas
      if (!stillRefresh) {
        // Logout automático
        mutationLogout();
        return Promise.reject(error);
      }
      await tryToRenewAccessToken(error);
    }
  }
);
```

**Padrão**: Se 401 ou 403:
1. Tenta renovar token (até 3x)
2. Se falhar: Logout automático
3. Redireciona para `/login`

#### Mecanismo 3: Session Validation na Inicialização

```typescript
// pages/AppInitPage/index.tsx
const { data: sessionData, isFetched: isSessionFetched } = 
  useGetAuthSession({
    enabled: isLoaded,
  });

// GET /session endpoint
// Valida se sessão ainda está ativa (via HttpOnly cookies)
// Restaura estado de autenticação se válido
```

**Padrão**: Na inicialização da app, valida sessão via HttpOnly cookies.

### 2.2 Abordagem de Langflow para Session Expiry (NÃO há modal overlay)

**Importante**: Langflow **NÃO implementa modal de aviso de expiry**

- ❌ Sem overlay "Sua sessão expirou"
- ❌ Sem modal "Clique aqui para re-autenticar"
- ✅ Em vez disso: Trata como erro silencioso nas requisições
- ✅ Próxima ação do usuário que dispara erro 401 → Logout

**Implicação para RID**: 
- Langflow usa abordagem **passiva** (não informa ao usuário preemptivamente)
- RID pode melhorar isto com **overlay/modal proativo** (DD-001 em Gate 1.5)

### 2.3 Heartbeat/Keep-Alive em Langflow

**Mecanismo de Keep-Alive**:

Langflow implementa keep-alive **apenas em SSE** (Server-Sent Events):

```typescript
// hooks/use-webhook-events.ts
const eventSource = new EventSource(sseUrl, { withCredentials: true });

eventSource.addEventListener('heartbeat', () => {
  // Keep-alive event — sem ação, apenas previne timeout
});
```

**Não há endpoint `/health` ou `/heartbeat` dedicado.**

**Padrão**: Refresh automático a cada ~54 min. Se usuário inativo, logout.

### 2.4 HTTP Status Codes para Session Expiry

```
401 Unauthorized  → Token inválido/expirado
403 Forbidden     → Token válido mas sem permissão / workspace inválido
500 Server Error  → NÃO faz logout (apenas reseta estado de build)
```

---

## 3. Endpoints da API Backend (Consumidos pelo Frontend)

### 3.1 Endpoints de Autenticação

| Método | Endpoint | Propósito | Autenticação |
|--------|----------|-----------|--------------|
| `POST` | `/login` | Login com credenciais | Nenhuma |
| `POST` | `/logout` | Logout (sem autoLogin) | HttpOnly |
| `POST` | `/refresh` | Renovar access token | HttpOnly |
| `GET` | `/session` | Validar sessão na init | HttpOnly |
| `POST` | `/auto_login` | Auto-login automático | Nenhuma |
| `GET` | `/users/user` | Info do usuário logado | Bearer/HttpOnly |
| `PATCH` | `/users/{id}` | Atualizar usuário | Bearer/HttpOnly |

### 3.2 Endpoints Principais de Flows

| Método | Endpoint | Propósito |
|--------|----------|-----------|
| `GET` | `/flows` | Listar flows |
| `POST` | `/flows` | Criar flow |
| `GET` | `/flows/{id}` | Obter flow específico |
| `PUT` | `/flows/{id}` | Atualizar flow |
| `DELETE` | `/flows/{id}` | Deletar flow |
| `GET` | `/flows/public_flow` | Acessar flows públicos |
| `POST` | `/build` | Executar build/run flow |
| `POST` | `/run/session` | Criar sessão de chat |
| `GET` | `/monitor/messages` | Histórico de mensagens |

### 3.3 Endpoints de Realtime (SSE)

| Endpoint | Propósito |
|----------|-----------|
| `GET /api/v1/webhook-events/{flowId}` | SSE para eventos de build |
| Eventos: `vertices_sorted`, `build_start`, `end_vertex`, `end`, `error`, `heartbeat` | Keep-alive + eventos |

### 3.4 Padrão de Response

**Success (2xx)**:
```json
{
  "data": { /* ... */ },
  "message": "Success"
}
```

**Error (4xx/5xx)**:
```json
{
  "detail": "Error message",
  "status": 400
}
```

---

## 4. Armazenamento de Credenciais

### 4.1 HttpOnly Cookies (Seguro)

**Gerenciados pelo Backend**, impossível acessar via JavaScript:
- `refresh_token` (HttpOnly, seguro contra XSS)

**Vantagem**: Browser envia automaticamente com `credentials: include`.

### 4.2 Acessível Cookies (via react-cookie)

**Acessível ao JavaScript**, gerado pelo Frontend:
- `access_token_lf`: Access token
- `auto_login_lf`: Flag de auto-login
- `apikey_tkn_lflw`: API key do usuário

### 4.3 localStorage

- `access_token_lf`: Duplicação (também em cookie)
- Questionável: duplicação desnecessária

**Recomendação para RID**: Usar **apenas HttpOnly cookies + localStorage** (não duplicar).

---

## 5. Stores Zustand em Langflow

### 5.1 authStore (Modelo)

```typescript
// src/stores/authStore.ts
interface AuthStoreType {
  isAdmin: boolean;
  isAuthenticated: boolean;
  accessToken: string | null;
  userData: Users | null;
  autoLogin: boolean | null;
  apiKey: string | null;
  authenticationErrorCount: number;
  
  // Actions
  logout(): void;
  setIsAdmin(isAdmin: boolean): void;
  setIsAuthenticated(authenticated: boolean): void;
  setAccessToken(token: string): void;
  setUserData(user: Users): void;
  setAutoLogin(autoLogin: boolean): void;
  setApiKey(apiKey: string): void;
  incrementAuthErrorCount(): void;
  resetAuthErrorCount(): void;
}

export const useAuthStore = create<AuthStoreType>((set) => ({
  isAdmin: false,
  isAuthenticated: false,
  accessToken: null,
  userData: null,
  autoLogin: null,
  apiKey: null,
  authenticationErrorCount: 0,
  
  logout: () => set({ 
    isAuthenticated: false, 
    accessToken: null,
    userData: null
  }),
  setIsAdmin: (isAdmin) => set({ isAdmin }),
  // ... outros setters
}));
```

### 5.2 sessionManagerStore (Para Flows)

```typescript
interface SessionManagerStoreType {
  flowId: string;
  activeSessionId: string;
  sessions: SessionInfo[];
  
  initialize(flowId: string): void;
  addSession(session: SessionInfo): void;
  syncFromServer(serverSessionIds: string[]): void;
}

export const useSessionManagerStore = create<SessionManagerStoreType>(...);
```

### 5.3 flowStore (Para State do Flow)

```typescript
interface FlowStoreType {
  flows: Flow[];
  currentFlowId: string;
  isBuilding: boolean;
  buildStatus: Record<string, BuildStatus>;
  
  // Actions
  addFlow(flow: Flow): void;
  updateFlow(id: string, updates: Partial<Flow>): void;
  deleteFlow(id: string): void;
  setIsBuilding(building: boolean): void;
  updateBuildStatus(vertexId: string, status: BuildStatus): void;
}

export const useFlowStore = create<FlowStoreType>(...);
```

---

## 6. Response Interceptor Pattern

### 6.1 Axios Interceptor (Langflow)

```typescript
// controllers/API/api.tsx
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true  // ← CRITICAL
});

api.interceptors.response.use(
  (response) => {
    setHealthCheckTimeout(null);  // Clear timeout
    return response;
  },
  async (error: AxiosError) => {
    // Detecta 401/403
    const isAuthError = error?.response?.status === 401 || 403;
    
    if (isAuthError && !isAutoLogin) {
      // Tenta renovar
      const stillRefresh = checkErrorCount();  // Max 3
      if (!stillRefresh) {
        // Logout
        mutationLogout();
        return Promise.reject(error);
      }
      
      // Retry com novo token
      return api.request(error.config);
    }
    
    return Promise.reject(error);
  }
);
```

---

## 7. Recomendações para MVP (Frontend Libs)

### 📦 Libs a USAR (Alinhado com Langflow)

| Lib | Versão | Escopo MVP |
|-----|--------|-----------|
| **React** | 19.2.1 | ✅ Core |
| **TypeScript** | 5.4.5 | ✅ Type safety |
| **Vite** | 7.3.1 | ✅ Build (já em uso) |
| **React Router DOM** | 6.23.1 | ✅ Routing + guards |
| **Zustand** | 4.5.2 | ✅ **Auth + UI state** |
| **Axios** | 1.7.4 | ✅ **HTTP client com interceptadores** |
| **Tailwind CSS** | 3.4.4 | ✅ Styling |
| **shadcn-ui** | 0.9.4 | ✅ Button, Card, Modal (base) |

### 🚫 Libs a EVITAR (Para MVP)

| Lib | Razão |
|-----|-------|
| **Redux** | Overkill; Zustand é mais simples |
| **Chakra UI** | Full UI library; Tailwind + shadcn é suficiente |
| **fetch nativo** | Use Axios (melhor interceptação) |
| **React Query** | Phase 2 (MVP não precisa de caching sofisticado) |

---

## 8. Implementação Recomendada: Session Expiry (Resposta Q3)

### 8.1 Estratégia Híbrida (Langflow + Improvement para RID)

**Fase 1: Langflow Pattern (MVP)**
1. ✅ Proactive refresh a cada ~54 min
2. ✅ Response interceptor para 401/403
3. ✅ Logout automático após 3 falhas de refresh
4. ✅ Validação de sessão na inicialização

**Fase 2: RID Improvement (Overlay)**
5. ⭐ Modal overlay avisando "Sessão expirada"
6. ⭐ Button "Re-autenticar" que leva a `/login?redirect=`

### 8.2 Implementação Técnica para MVP

**Arquivo**: `frontend/apps/rockitdown/src/stores/authStore.ts`

```typescript
import create from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface AuthStoreType {
  isAuthenticated: boolean;
  accessToken: string | null;
  userData: any | null;
  autoLogin: boolean | null;
  authErrorCount: number;
  sessionExpired: boolean;
  
  // Actions
  setAuthenticated(auth: boolean): void;
  setAccessToken(token: string): void;
  setUserData(user: any): void;
  setAutoLogin(auto: boolean): void;
  incrementErrorCount(): void;
  resetErrorCount(): void;
  setSessionExpired(expired: boolean): void;
  logout(): void;
}

export const useAuthStore = create<AuthStoreType>(
  subscribeWithSelector((set) => ({
    isAuthenticated: false,
    accessToken: null,
    userData: null,
    autoLogin: null,
    authErrorCount: 0,
    sessionExpired: false,
    
    setAuthenticated: (auth) => set({ isAuthenticated: auth }),
    setAccessToken: (token) => set({ accessToken: token }),
    setUserData: (user) => set({ userData: user }),
    setAutoLogin: (auto) => set({ autoLogin: auto }),
    incrementErrorCount: () => set((state) => ({
      authErrorCount: state.authErrorCount + 1
    })),
    resetErrorCount: () => set({ authErrorCount: 0 }),
    setSessionExpired: (expired) => set({ sessionExpired: expired }),
    logout: () => set({
      isAuthenticated: false,
      accessToken: null,
      userData: null,
      authErrorCount: 0,
      sessionExpired: false
    })
  }))
);
```

**Arquivo**: `frontend/apps/rockitdown/src/api/axios-client.ts`

```typescript
import axios, { AxiosError } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = process.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // ← CRITICAL para HttpOnly cookies
});

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const isAuthError = error?.response?.status === 401 || 403;
    const isAutoLogin = useAuthStore.getState().autoLogin;
    
    if (isAuthError && !isAutoLogin) {
      const authStore = useAuthStore.getState();
      authStore.incrementErrorCount();
      
      if (authStore.authErrorCount >= 3) {
        // Logout após 3 falhas
        authStore.setSessionExpired(true);
        authStore.logout();
        window.location.href = '/login?redirect=' + window.location.pathname;
        return Promise.reject(error);
      }
      
      // Tenta renovar token
      try {
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/langflow/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        const newToken = refreshResponse.data?.access_token;
        if (newToken) {
          authStore.setAccessToken(newToken);
          authStore.resetErrorCount();
          
          // Retry original request
          return apiClient.request(error.config!);
        }
      } catch (refreshError) {
        authStore.setSessionExpired(true);
        authStore.logout();
        window.location.href = '/login?redirect=' + window.location.pathname;
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

**Arquivo**: `frontend/apps/rockitdown/src/hooks/useSessionRefresh.ts`

```typescript
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/api/axios-client';

const ACCESS_TOKEN_EXPIRE_SECONDS = 
  Number(process.env.VITE_ACCESS_TOKEN_EXPIRE_SECONDS || 3600);
const REFRESH_INTERVAL = ACCESS_TOKEN_EXPIRE_SECONDS * 0.9 * 1000;  // 90%

export function useSessionRefresh() {
  const { isAuthenticated, autoLogin } = useAuthStore();
  
  useEffect(() => {
    if (!isAuthenticated || autoLogin) {
      return;
    }
    
    const interval = setInterval(async () => {
      try {
        const response = await apiClient.post('/langflow/auth/refresh', {});
        const newToken = response.data?.access_token;
        if (newToken) {
          useAuthStore.setState({ accessToken: newToken });
        }
      } catch (error) {
        // Interceptor já trata logout
        console.error('Token refresh failed:', error);
      }
    }, REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, [isAuthenticated, autoLogin]);
}
```

### 8.3 Componente de Overlay (Phase 2)

```typescript
// frontend/apps/rockitdown/src/components/SessionExpiryModal.tsx
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';

export function SessionExpiryModal() {
  const sessionExpired = useAuthStore((state) => state.sessionExpired);
  
  if (!sessionExpired) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm shadow-lg">
        <h2 className="text-lg font-bold mb-4">Sessão Expirada</h2>
        <p className="text-gray-600 mb-6">
          Sua sessão expirou. Por favor, faça login novamente.
        </p>
        <button
          onClick={() => {
            useAuthStore.getState().logout();
            window.location.href = '/login?redirect=' + window.location.pathname;
          }}
          className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
        >
          Fazer Login Novamente
        </button>
      </div>
    </div>
  );
}

// Em App.tsx:
// <SessionExpiryModal />
```

---

## 9. Checklist de Implementação

- [ ] Instalar `zustand` (4.5.2)
- [ ] Instalar `axios` (1.7.4)
- [ ] Remover `react-router-dom` v7 e usar v6.23.1 (alinhado com Langflow)
- [ ] Criar `authStore.ts` com Zustand
- [ ] Criar `axios-client.ts` com interceptadores
- [ ] Criar `useSessionRefresh.ts` hook
- [ ] Criar `ProtectedRoute.tsx` com guard
- [ ] Criar `SessionExpiryModal.tsx` (Phase 2)
- [ ] Testes para auth store + interceptor

---

## 10. Conclusão & Resposta a Q3

### ✅ Pergunta Original
**Q3: Como Langflow lida com session expiry?**

### ✅ Resposta
1. **Proactive Refresh**: Token renovado a cada ~54 min (90% do tempo de expiração)
2. **Reativo (401/403)**: Response interceptor detecta erro e tenta renovar
3. **Max 3 Retries**: Após 3 falhas, logout automático
4. **Sem Modal**: Langflow não avisa ao usuário; apenas faz logout silenciosamente
5. **Validação na Init**: `GET /session` confirma sessão ao carregar app

### ⭐ Recomendação para RID
- **MVP**: Use exato padrão Langflow (proactive + reativo + logout)
- **Phase 2**: Adicionar modal overlay para UX melhor (não deixa usuário surpreso)

### 📦 Libs a Usar
- `zustand` 4.5.2 (auth store)
- `axios` 1.7.4 (HTTP com interceptadores)
- `react-router-dom` 6.23.1 (roteamento + guards)
- `tailwind` + `shadcn-ui` (UI)

---

**Documento pronto para GATE 1 & 3 refinement.**
