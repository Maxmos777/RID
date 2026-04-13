---
feature: rid-langflow-single-entry
module: frontend
filtered_from: docs/pre-dev/rid-langflow-single-entry/gate-7-tasks.md
---

# Frontend Tasks — Entrada única autenticada para o editor de fluxos (RID)

> This file contains only tasks with **target: frontend**.
> Full task index (all targets): `/home/RID/docs/pre-dev/rid-langflow-single-entry/gate-7-tasks.md`

---

## Frontend task summary

| Task | Title | Hours | Confidence | Requires | Blocks | Status |
|------|-------|-------|-----------|---------|--------|--------|
| T-005 | Session Expiry Overlay + heartbeat hook | 5h | High | T-001, T-002, T-003 | T-006 | ⏸️ Pending |

**Frontend total estimated effort:** 5h

---

## Context for frontend agent

**Feature goal:** Close direct public access to the Langflow editor (port 7861) and route all traffic through a single authenticated entry point. The frontend's responsibility in this feature is a single new component: a session expiry overlay shown when the user's Django session expires while they are actively using the editor.

**Key architectural decisions relevant to frontend:**
- **DD-001:** Session expiry is detected by client-side heartbeat polling, NOT by intercepting proxy redirects. Traefik returns 302 to the browser for navigation — the overlay is activated by the client.
- **DD-004:** No external UI component library. Raw React 18 + inline styles or plain CSS only.
- **DD-005:** WCAG 2.1 AA required on all new components.
- **Known WebSocket limitation (TRD §7.3):** WebSocket connections are NOT terminated when session expires. The overlay is activated by HTTP heartbeat only. This is accepted MVP behavior — do not implement WebSocket session detection.

**Endpoint contract (implemented by T-003 — backend):**

| Code | Meaning |
|------|---------|
| 200 | Session valid + correct tenant |
| 401 | Session absent or expired — **trigger overlay** |
| 403 | Wrong tenant — silent (no overlay) |

**Backend dependencies:** T-001 (Traefik routes `/internal/auth-check/`), T-002 (session cookies sent correctly), T-003 (endpoint returns 401/200/403).

---

## T-005 — Session Expiry Overlay + heartbeat hook

**Target:** frontend  
**Working Directory:** `/home/RID/frontend`  
**Agent:** `ring:frontend-engineer`  
**Size:** M (5h)

**Deliverable:** A `SessionExpiryOverlay` React component and `useSessionHeartbeat` custom hook are integrated into the RID shell — polling `GET /internal/auth-check/` every 120 seconds, displaying a WCAG-compliant "Sessão expirada" overlay with "Entrar novamente" CTA on 401, and automatically cancelling the heartbeat when the user leaves the editor.

---

### Scope

**Includes:**
- `useSessionHeartbeat.ts` hook (separate file — standard: hooks > 20 lines in own file):
  - `useEffect` + `setInterval` at 120s (120_000ms) interval
  - `fetch('/internal/auth-check/', { credentials: 'same-origin' })`
  - Calls `onSessionExpired()` callback **only on HTTP 401**
  - Network errors are **silent** (no overlay on transient failures)
  - HTTP 403 is **silent** (different condition — wrong tenant, not expired session)
  - `clearInterval` in `useEffect` cleanup (prevents memory leaks and ghost polling after unmount)
- `SessionExpiryOverlay.tsx` component:
  - Full-screen overlay rendered on top of editor content
  - Message "Sessão expirada" + supporting copy in pt-BR
  - CTA "Entrar novamente" → `window.location.href = '/login/?next=/flows/'`
  - No dismiss/close action (user must re-authenticate by design — security requirement)
  - WCAG: `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"`
  - Focus trap: focus moves to overlay on open; Tab cycles within overlay only; Enter activates CTA
  - Inline styles or plain CSS — no external component library (DD-004)
- Integration into RID shell: mount `SessionExpiryOverlay` in the shell component wrapping the Langflow editor route; heartbeat active only when editor is mounted

**Excludes:**
- Auth Check Endpoint implementation (backend — T-003)
- Backend proxy settings (backend — T-002)
- Traefik configuration (infra — T-001)
- WebSocket session expiry detection — out of MVP scope (TRD §7.3 known limitation)
- Overlay dismissal without re-authentication — intentionally excluded (security)
- Any changes to the Langflow editor itself

---

### Success Criteria

**Functional:**
- Overlay appears within 120 seconds of session expiry (next heartbeat tick)
- "Entrar novamente" CTA redirects to `/login/?next=/flows/`
- Heartbeat `clearInterval` called on component unmount — no network requests after unmount
- Network errors during heartbeat do NOT show overlay
- HTTP 403 does NOT show overlay (only HTTP 401)

**Technical:**
- Hook exported from `useSessionHeartbeat.ts` (own file, not inlined in component)
- `credentials: 'same-origin'` on all fetch calls (session cookie transmitted)
- Zero new npm dependencies added
- No `useEffect` for conventional data fetching (heartbeat exception justified: infrastructure polling, not data — see dependency-map §5.3)

**Quality (WCAG 2.1 AA):**
- `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"` present in rendered HTML
- Focus moves to overlay on open
- Focus trapped inside overlay while mounted
- Tab navigation cycles only through overlay interactive elements
- Enter key activates "Entrar novamente" CTA
- Contrast >= 4.5:1 on all overlay text
- "Entrar novamente" touch target >= 44×44px on mobile (375px viewport)
- axe-core scan: 0 critical WCAG violations

---

### User Value
Users working in the editor for extended sessions are proactively warned before being abruptly redirected, allowing them to save work and re-authenticate without confusion.

### Technical Value
Implements the client-side session expiry detection pattern (DD-001) that avoids relying on Traefik's 302 redirect during active editor use. Cancels cleanly on unmount — no memory leaks, no ghost polling.

### Technical Components (TRD)
- Component 3 — Session Expiry Overlay (Frontend SPA)

---

### Dependencies

**Blocks:** T-006 (overlay scenario in integration tests requires this component deployed)

**Requires:**
- T-001 (Traefik routes `/internal/auth-check/` to Django — required for integration testing)
- T-002 (secure session cookies required for heartbeat to carry session correctly)
- T-003 (endpoint must exist and return 401 on expired session)

**Development note:** `useSessionHeartbeat.ts` and `SessionExpiryOverlay.tsx` can be implemented and unit-tested locally before T-001/T-002/T-003 are merged — mock `fetch` in unit tests. Full integration testing requires T-001 + T-002 + T-003.

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| `useSessionHeartbeat.ts` hook | 1h | setInterval, fetch, cleanup, 401 detection only |
| `SessionExpiryOverlay.tsx` component structure | 1h | Overlay layout, pt-BR copy, CTA |
| Inline styles / plain CSS for overlay | 0.5h | Full-screen, z-index, background, contrast |
| WCAG attributes + focus trap implementation | 0.75h | role, aria-modal, aria-live, focus management |
| Shell integration (mount in editor route) | 0.5h | Identify mount point in existing shell |
| Unit tests (hook + component) | 0.75h | jest + @testing-library/react |

**Total: 5h — Confidence: High**

Rationale: implementation pattern fully specified in gate-6-dependency-map.md §5.1–5.3. No design ambiguity. Risk is low — pure React 18 with browser APIs only.

---

### Implementation reference

From `gate-6-dependency-map.md` §5.2 — canonical hook pattern:

```typescript
// useSessionHeartbeat.ts
useEffect(() => {
  const intervalId = setInterval(async () => {
    try {
      const response = await fetch('/internal/auth-check/', {
        credentials: 'same-origin',
      });
      if (response.status === 401) {
        onSessionExpired();
      }
    } catch {
      // Network error — silent; do not trigger overlay
    }
  }, 120_000);

  return () => clearInterval(intervalId); // mandatory cleanup
}, [onSessionExpired]);
```

**Key decisions:**
- `credentials: 'same-origin'` — session cookie sent to same domain
- Silent catch — no overlay for transient network failures
- Only 401 triggers overlay (not 403, not 5xx, not network error)
- Interval is 120s (2 minutes) — matches TRD Component 3 spec

---

### Testing Strategy

**Unit tests — hook (`useSessionHeartbeat.ts`):**
- Mock `fetch` to return `{ status: 401 }` → assert `onSessionExpired` called after interval tick (use `jest.useFakeTimers()`)
- Mock `fetch` to throw `TypeError: Failed to fetch` → assert `onSessionExpired` NOT called
- Mock `fetch` to return `{ status: 403 }` → assert `onSessionExpired` NOT called
- Unmount hook → assert no pending timers (jest timer inspection)

**Unit tests — component (`SessionExpiryOverlay.tsx`):**
- Render component → assert `role="alertdialog"` in DOM
- Render component → assert `aria-modal="true"` in DOM
- Render component → assert `aria-live="assertive"` in DOM
- Click "Entrar novamente" → assert `window.location.href` set to `/login/?next=/flows/`
- axe-core (`jest-axe`): render component → assert 0 critical violations

**Integration test (requires T-001 + T-002 + T-003 — coordinated with T-006):**
- Playwright: load editor with valid session → expire session server-side → advance timer (`page.clock.tick(120_000)`) → assert overlay element visible with correct `role`

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Traefik returns 302 instead of 401 for `fetch()` heartbeat | Low | High | `fetch()` with `credentials: 'same-origin'` follows redirects by default; add `redirect: 'manual'` if needed and treat opaque response as non-401 (no overlay). Verify behavior with T-003 endpoint directly. |
| Focus trap breaks existing editor keyboard navigation | Low | Medium | Focus trap scoped to overlay only; deactivated when overlay is not mounted |
| React StrictMode double-invoke creates two intervals | Low | Low | `useEffect` cleanup correctly cancels interval; test with StrictMode enabled |
| `onSessionExpired` callback reference changes on every render (stale closure) | Medium | Low | Memoize callback with `useCallback` at call site; or use `useRef` inside hook |

---

### Definition of Done

- [ ] `useSessionHeartbeat.ts` hook in its own file
- [ ] `credentials: 'same-origin'` on fetch; 120s (120_000ms) interval
- [ ] Only HTTP 401 triggers `onSessionExpired()` callback
- [ ] Network errors and HTTP 403 are silent
- [ ] `clearInterval` called on unmount
- [ ] `SessionExpiryOverlay.tsx` component with pt-BR copy
- [ ] "Entrar novamente" CTA → `window.location.href = '/login/?next=/flows/'`
- [ ] `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"` in rendered HTML
- [ ] Focus moves to overlay on open; focus trap active while mounted
- [ ] Zero new npm dependencies added
- [ ] Hook unit tests pass: 401 trigger, error silence, 403 silence, cleanup
- [ ] Component unit tests pass: ARIA attrs, CTA redirect behavior
- [ ] axe-core (`jest-axe`): 0 critical violations
- [ ] Contrast >= 4.5:1 verified (browser DevTools or Lighthouse)
- [ ] Touch target of "Entrar novamente" >= 44×44px at 375px viewport
- [ ] Shell integration: heartbeat active only when editor is mounted
