---
title: GATE 2 vs GATE 3 - Semantic Alignment Audit
date: 2026-04-13
status: draft
---

# GATE 2 vs GATE 3 - Semantic Alignment Audit

## Objetivo
Validar que GATE 3 (TRD) cobre **todas as 9 features** mapeadas em GATE 2 (Feature Map) de forma coerente e sem inconsistências.

---

## GATE 2 Features (Expected in GATE 3)

| Feature | GATE 2 Description | GATE 2 Est. | GATE 3 Coverage | Status |
|---------|-------------------|------------|------------------|--------|
| **F1** | Backend Flows List Endpoint | 4-6h | ✅ Section 1 (Endpoint Spec) | **Covered** |
| **F2** | Session Management (Zustand + Axios) | 3-4h | ⚠️ Implied but not explicit | **Missing** |
| **F3** | React Router + Protected Routes | 2-3h | ⚠️ Mentioned implicitly | **Incomplete** |
| **F4** | FlowsList Component + Pagination | 4-5h | ✅ Section 2.2 (Components) | **Covered** |
| **F5** | Navigation to Langflow Editor | 1-2h | ✅ Section 3 (Flow 2: handleEditFlow) | **Covered** |
| **F6** | Context Persistence (sessionStorage) | 2-3h | ✅ Section 2.2 (useFlowsContext) | **Covered** |
| **F7a** | Unit + Component Tests | 4-5h | ⚠️ Mixed with F7b | **Incomplete** |
| **F7b** | Integration + E2E Tests | 4-5h | ⚠️ Mixed with F7a | **Incomplete** |
| **F8** | Styling (Tailwind Setup) | 2-3h | ❌ Not mentioned | **Missing** |
| **F9** | Error Handling Strategy | 2-3h | ⚠️ Mentioned case-by-case | **Incomplete** |

---

## Detailed Inconsistencies

### 1. ❌ Feature 2: Session Management (Zustand + Axios)

**GATE 2 Says:**
```
Feature 2: Frontend Session Management
- Zustand authStore: state management
- Axios interceptor: detect 401/403, retry, logout after 3 failures
- useSessionRefresh: proactive token refresh (~54 min)
- Retry logic: exponential backoff
- P0 Blocker: src/types/stores.ts with type contracts
```

**GATE 3 TRD Says:**
```
Section 2.2: useFlows hook uses fetch() with basic error handling
- No mention of authStore or Zustand
- No mention of Axios interceptor
- No mention of useSessionRefresh
- No mention of src/types/stores.ts
```

**Issue:** TRD shows fetch() in pseudocode but GATE 2 specifies Axios + interceptor + Zustand stores.

**Resolution Required:**
1. Add Section 2.3: "Session Management Architecture"
   - Describe Zustand authStore (state machine)
   - Describe Axios client configuration with interceptor
   - Describe useSessionRefresh hook for proactive refresh
   - Link to src/types/stores.ts type contracts

2. Update useFlows pseudocode to use Axios instead of fetch

3. Add Zustand store implementations (authStore, sessionStore)

---

### 2. ⚠️ Feature 3: React Router Setup

**GATE 2 Says:**
```
Feature 3: Frontend Routing & Protected Routes
- React Router 6.23.1
- ProtectedRoute component (auth guard)
- Route config: /app/flows → FlowsPage
- Layout wrapper with sidebar
```

**GATE 3 TRD Says:**
```
Section 2.1: Folder structure mentions FlowsPage.tsx and App.tsx
Section 3: Diagrams show navigation but no Router setup
```

**Issue:** TRD assumes routes exist but doesn't specify how to set up BrowserRouter, Routes, <Outlet>, etc.

**Resolution Required:**
1. Add Section 2.0: "Frontend Architecture & Routing"
   - BrowserRouter setup in main.tsx
   - App.tsx refactor with Routes and Outlet
   - ProtectedRoute component spec
   - Route configuration table

---

### 3. ⚠️ Feature 7a vs 7b: Testing Split

**GATE 2 Says:**
```
Feature 7a: Unit + Component Tests (4-5h)
- Unit tests: hooks (useFlows, useFlowsContext, useSessionRefresh)
- Component tests: FlowsList, FlowCard, ProtectedRoute
- Scope: Isolated, mocked dependencies
- Parallelizable with Feature 4

Feature 7b: Integration + E2E Tests (4-5h)
- Integration: Backend endpoint + Langflow mock
- E2E: Full flow login → flows list → navigate → back
- Multi-tenant isolation verification
- After Feature 6 complete
```

**GATE 3 TRD Says:**
```
Section 4: "Testing Strategy"
- Tests mixed without phase separation
- Includes useFlows, useFlowsContext, FlowsList tests
- Includes backend integration tests
- No explicit 7a/7b split or execution order
```

**Issue:** TRD doesn't distinguish 7a (can run in parallel with Feature 4) vs 7b (sequential after Feature 6).

**Resolution Required:**
1. Reorganize Section 4 into subsections:
   - 4.1: Feature 7a - Unit + Component Tests
     * useFlows hook tests
     * useSessionRefresh hook tests
     * useFlowsContext hook tests
     * FlowsList component tests
     * FlowCard component tests
     * ProtectedRoute component tests
   
   - 4.2: Feature 7b - Integration + E2E Tests
     * Backend endpoint integration test
     * Full user flow E2E test (login → flows → navigate → back)
     * Multi-tenant isolation test
     * Error recovery tests

2. Add execution order note: "7a runs in parallel with Feature 4; 7b runs after Feature 6"

3. Add test execution command examples for both phases

---

### 4. ❌ Feature 8: Styling (Tailwind)

**GATE 2 Says:**
```
Feature 8: Styling (Tailwind Setup)
- Install: tailwindcss, postcss, autoprefixer
- Create: tailwind.config.ts, postcss.config.ts, src/index.css
- Scope: Sidebar, Flow cards, Session overlay
- Estimate: 2-3 hours
```

**GATE 3 TRD Says:**
```
No mention of Tailwind setup
Only inline examples with className attributes
```

**Issue:** TRD omits Tailwind setup entirely. Frontend needs Tailwind to render components.

**Resolution Required:**
1. Add Section 3.0: "Frontend Styling Strategy"
   - Tailwind installation steps
   - Configuration files (tailwind.config.ts, postcss.config.ts)
   - Utility classes for components
   - Responsive design approach

2. Update component examples with actual Tailwind classes

---

### 5. ⚠️ Feature 9: Error Handling

**GATE 2 Says:**
```
Feature 9: Error Handling Strategy
- Global error boundary
- Toast/snackbar notifications
- Retry mechanisms
- 401 auto-logout
- Estimate: 2-3 hours
```

**GATE 3 TRD Says:**
```
Section 1.4: HTTP error status table (401, 403, 404, 503)
Section 2.2: useFlows hook handles errors case-by-case
No mention of ErrorBoundary or global strategy
```

**Issue:** TRD treats error handling per-feature instead of defining global strategy.

**Resolution Required:**
1. Add Section 3.1: "Global Error Handling Strategy"
   - ErrorBoundary for uncaught exceptions
   - Toast notification system (which library? shadcn-ui Toast?)
   - Retry strategies per error type (exponential backoff for 503, redirect for 401, etc.)
   - Session expiry overlay (already exists)

2. Reference existing session expiry overlay component

---

### 6. ⚠️ src/types/stores.ts (Type Contracts - P0 Blocker)

**GATE 2 Says:**
```
Feature 2: P0 Blocker Note
- src/types/stores.ts MUST exist before Feature 2 implementation
- Contains: AuthStoreState, SessionStoreState, FlowStoreState, ContextStoreState
- This is a code review blocker if types are undefined
```

**Status:** ✅ File created at `/home/RID/frontend/apps/rockitdown/src/types/stores.ts` 

**But GATE 3 TRD:** Never references stores.ts or mentions these type contracts.

**Issue:** TRD assumes Zustand stores exist but doesn't reference the type contracts.

**Resolution Required:**
1. Add to Section 2.3 (Session Management Architecture):
   ```
   Type Contracts (src/types/stores.ts):
   - AuthStoreState: isAuthenticated, userId, email, accessToken, refreshToken, etc.
   - SessionStoreState: isRefreshing, lastRefreshAt, nextRefreshAt, etc.
   - FlowStoreState: flows[], loading, error, currentPage, selectedFlowId
   - ContextStoreState: flowsListContext (page, scroll, timestamp)
   
   (Already defined in /home/RID/frontend/apps/rockitdown/src/types/stores.ts)
   ```

2. Reference the existing file in TRD

---

## Summary: GATE 2 ↔ GATE 3 Alignment Issues

| Issue | Severity | Impact | Resolution |
|-------|----------|--------|-----------|
| Feature 2 (Zustand + Axios) missing | **Critical** | useFlows uses fetch instead of Axios; authStore undefined | Add Section 2.3 with store specs |
| Feature 3 (React Router) incomplete | **High** | App.tsx doesn't have Routes; BrowserRouter not setup | Add Section 2.0 with router config |
| Feature 7a/7b split unclear | **High** | Tests not divided into phases; can't parallelize | Reorganize Section 4 into 7a/7b |
| Feature 8 (Tailwind) missing | **High** | No CSS framework specified; styling incomplete | Add Section 3.0 with Tailwind setup |
| Feature 9 (Error Handling) incomplete | **Medium** | No global strategy; error handling scattered | Add Section 3.1 with error strategy |
| src/types/stores.ts not referenced | **Medium** | Type contracts exist but not documented in TRD | Reference in Section 2.3 |

---

## Recommended GATE 3 TRD Refactor

**Current Structure:**
```
1. Backend Endpoint Spec
2. Frontend Architecture
3. Data Flow Diagrams
4. Testing Strategy
5. ADR Compliance
6. Security Considerations
7. Next Steps
```

**Proposed Structure:**
```
1. Backend Endpoint Spec (Feature 1) ← unchanged
2. Frontend Architecture & Routing (Feature 3 + type setup)
   2.0: React Router Setup
   2.1: Folder Structure
   2.2: Components & Hooks (Features 4, 5, 6)
   2.3: Session Management (Feature 2)
   2.4: Error Handling & Toast (Feature 9)
3. Styling Strategy (Feature 8)
4. Data Flow Diagrams (unchanged)
5. Testing Strategy (Features 7a, 7b split)
   5.1: Feature 7a - Unit + Component Tests
   5.2: Feature 7b - Integration + E2E Tests
6. ADR Compliance (unchanged)
7. Security Considerations (unchanged)
8. Type Contracts Reference (src/types/stores.ts)
9. Critical Path & Execution Order
10. Next Steps
```

---

## P0 Blockers Before Implementation

### ❌ Must Fix in GATE 3 TRD

1. **Zustand + Axios Integration**: Add full Section 2.3
   - authStore specification
   - sessionStore specification  
   - Axios client with interceptor
   - useSessionRefresh hook spec
   
2. **React Router Setup**: Add Section 2.0
   - BrowserRouter in main.tsx
   - App.tsx Routes and Outlet
   - ProtectedRoute implementation
   
3. **Testing Phase Split**: Reorganize Section 4
   - Separate 7a (unit/component) from 7b (integration/e2e)
   - Add execution order and parallelization notes
   
4. **Tailwind Setup**: Add Section 3
   - Configuration files
   - Utility class strategy
   - Component styling examples
   
5. **Global Error Handling**: Add Section 3.1
   - ErrorBoundary component
   - Toast notification system
   - Retry strategy per error type

### ✅ Already Complete

- [ ] ADR Compliance Checklist (gate-2-adr-compliance-checklist.md)
- [ ] Type Contracts (src/types/stores.ts)
- [ ] Security Vulnerabilities (fixed in gate 3.5)
- [ ] Backend Endpoint Spec (Section 1)
- [ ] Component Pseudocode (Section 2.2)
- [ ] Testing Examples (Section 4)

---

## Next Step

**Action:** Refactor GATE 3 TRD to incorporate all 9 features + missing sections.

**Timeline:** 2-3 hours to revise and align documentation.

**Success Criteria:**
- [ ] All 9 features documented with explicit coverage
- [ ] GATE 2 Feature Map 1:1 mapping in GATE 3 TRD
- [ ] Testing strategy divided into 7a/7b phases
- [ ] Router, Zustand, Axios, Tailwind specs included
- [ ] Error handling strategy defined globally
- [ ] Type contracts referenced
- [ ] Critical path and execution order documented
