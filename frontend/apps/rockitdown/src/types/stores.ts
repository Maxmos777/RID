/**
 * Zustand Store Type Contracts
 *
 * Defines explicit TypeScript interfaces for all Zustand stores.
 * P0 Blocker Requirement (GATE 2): Must exist before Feature 2 implementation.
 * Used by: Feature 2 (Session Management), Feature 7a (Unit/Component Tests)
 */

/**
 * AuthStoreState - Authentication and session state
 *
 * Manages:
 * - User authentication status
 * - API tokens (access_token, refresh_token)
 * - Session validation state
 * - Error tracking for auto-logout after 3 failures
 */
export interface AuthStoreState {
  // Identity
  isAuthenticated: boolean;
  userId?: string;
  email?: string;

  // Tokens
  accessToken?: string;
  refreshToken?: string;
  tokenExpiresAt?: number; // Unix timestamp (ms)

  // Session state
  isSessionValid: boolean;
  lastRefreshAt?: number; // Unix timestamp (ms)

  // Error tracking
  failedRefreshAttempts: number; // Increments on 401/403; resets on 200
  maxFailedRefreshAttempts: number; // Default: 3

  // Actions
  setAuthenticated: (isAuth: boolean) => void;
  setTokens: (access: string, refresh: string, expiresAt: number) => void;
  setSessionValid: (valid: boolean) => void;
  incrementErrorCount: () => void;
  resetErrorCount: () => void;
  logout: () => void;

  // Computed (optional, for derived state)
  getTokenExpiresSoon: () => boolean; // True if expires within 10 min
}

/**
 * SessionStoreState - Session refresh and validation
 *
 * Manages:
 * - Proactive token refresh interval (~54 min)
 * - Last session validation timestamp
 * - Session refresh status (pending/success/error)
 */
export interface SessionStoreState {
  // Refresh state
  isRefreshing: boolean;
  lastRefreshTimestamp?: number; // Unix timestamp (ms)
  nextRefreshAt?: number; // Unix timestamp (ms) - calculated as now + 54min

  // Validation state
  isValidating: boolean;
  lastValidationAt?: number; // Unix timestamp (ms)
  validationError?: string;

  // Configuration
  refreshIntervalMs: number; // Default: 54 * 60 * 1000 (54 min)
  validationIntervalMs: number; // Default: 5 * 60 * 1000 (5 min)

  // Actions
  startRefresh: () => void;
  endRefresh: (success: boolean, error?: string) => void;
  setNextRefresh: (timestampMs: number) => void;
  startValidation: () => void;
  endValidation: (success: boolean, error?: string) => void;
  resetSession: () => void;

  // Computed
  shouldRefreshNow: () => boolean; // True if nextRefreshAt <= now
  isSessionHealthy: () => boolean; // True if validating recent + no errors
}

/**
 * FlowStoreState - Flows data and UI state
 *
 * Manages:
 * - List of flows from Langflow API
 * - Pagination and filtering
 * - Loading/error states
 * - Current flow selection
 */
export interface FlowStoreState {
  // Data
  flows: Array<{
    id: string;
    name: string;
    description: string;
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
  }>;

  // Pagination
  currentPage: number; // 0-indexed
  pageSize: number; // Default: 12
  totalCount: number;

  // Selection
  selectedFlowId?: string;

  // Loading state
  isLoading: boolean;
  isInitialized: boolean;

  // Error state
  error?: {
    code: number; // 401, 403, 503, etc.
    message: string;
    timestamp: number; // Unix timestamp (ms)
  };

  // Workspace context
  workspaceId?: string;

  // Actions
  setFlows: (flows: FlowStoreState['flows']) => void;
  setLoading: (loading: boolean) => void;
  setError: (code: number, message: string) => void;
  clearError: () => void;
  setCurrentPage: (page: number) => void;
  setSelectedFlow: (flowId: string) => void;
  setWorkspaceId: (id: string) => void;
  reset: () => void;

  // Computed
  getPaginatedFlows: () => FlowStoreState['flows']; // Returns flows for current page
  getTotalPages: () => number; // Math.ceil(totalCount / pageSize)
  hasError: () => boolean; // True if error exists
}

/**
 * ContextStoreState - UI context preservation (sessionStorage)
 *
 * Manages:
 * - Current page and scroll position
 * - UI state for recovery after navigation
 * - TTL for context expiry (30 min)
 */
export interface ContextStoreState {
  // Context data
  currentPage?: number;
  scrollPosition?: number; // Y-axis scroll
  flowsListContext?: {
    page: number;
    scroll: number;
    timestamp: number; // Unix timestamp (ms)
  };

  // Metadata
  contextExpiryMs: number; // Default: 30 * 60 * 1000 (30 min)
  lastSavedAt?: number; // Unix timestamp (ms)

  // Actions
  saveContext: (page: number, scroll: number) => void;
  restoreContext: () => ContextStoreState['flowsListContext'] | null; // Null if expired
  clearContext: () => void;

  // Computed
  isContextExpired: () => boolean; // True if saved > 30 min ago
  getContextAge: () => number; // Milliseconds since last save
}

/**
 * Store Hook Export Type
 *
 * Exported as useAuthStore(), useSessionStore(), useFlowStore(), useContextStore()
 * from ./hooks/useStores.ts or individual hook files.
 */
export type AuthStore = import('zustand').StoreApi<AuthStoreState>;
export type SessionStore = import('zustand').StoreApi<SessionStoreState>;
export type FlowStore = import('zustand').StoreApi<FlowStoreState>;
export type ContextStore = import('zustand').StoreApi<ContextStoreState>;
