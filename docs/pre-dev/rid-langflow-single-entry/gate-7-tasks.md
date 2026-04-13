---
feature: rid-langflow-single-entry
gate: 7
date: 2026-04-06
topology:
  structure: monorepo
  backend_path: /home/RID
  frontend_path: /home/RID/frontend
---

# Task Breakdown — Entrada única autenticada para o editor de fluxos (RID)

## Summary table

| Task | Title | Type | Est. Hours | Confidence | Blocks | Status |
|------|-------|------|-----------|-----------|--------|--------|
| T-001 | Traefik container + docker-compose integration | shared/infra | 4h | High | T-002, T-003, T-004, T-005, T-006 | ⏸️ Pending |
| T-002 | Django proxy header settings | backend | 2h | High | T-003, T-005 | ⏸️ Pending |
| T-003 | Auth Check Endpoint | backend | 5h | High | T-005, T-006 | ⏸️ Pending |
| T-004 | Error Page Template + Django view | backend | 4h | High | T-006 | ⏸️ Pending |
| T-005 | Session Expiry Overlay + heartbeat hook | frontend | 5h | High | T-006 | ⏸️ Pending |
| T-006 | Integration + E2E tests | shared/qa | 6h | Medium | — | ⏸️ Pending |

**Total estimated effort:** 26h  
**Critical path:** T-001 → T-002 → T-003 → T-005 → T-006

---

## Business Deliverables

| Task | Deliverable (plain language) |
|------|------------------------------|
| T-001 | The Langflow editor is no longer directly accessible on port 7861; all traffic routes through a single authenticated entry point |
| T-002 | Django correctly identifies the real user domain and enforces secure cookies when running behind the proxy |
| T-003 | The platform can confirm whether a user's session is valid and belongs to the correct tenant before granting access to the editor |
| T-004 | When the editor is unavailable, users see a branded RID error page with clear recovery actions instead of a generic proxy error |
| T-005 | Users working in the editor are notified with an overlay when their session expires, without losing their place in the application |
| T-006 | All security and access scenarios are automatically verified: unauthenticated access, session expiry, tenant isolation, and editor unavailability |

---

## T-001 — Traefik container + docker-compose integration

**Target:** shared/infra  
**Working Directory:** `/home/RID`  
**Agent:** `ring:devops-engineer`  
**Size:** M (4h)

**Deliverable:** Traefik v3.3.6 is running as the sole public entry point for `/flows/*`, with forwardAuth middleware wired to the Django auth-check endpoint, Langflow's port 7861 removed from public exposure, WebSocket headers passed through, and all configuration expressed as Docker labels in `docker-compose.yml`.

---

### Scope

**Includes:**
- Add `traefik:v3.3.6` service to `docker-compose.yml` under `langflow` profile
- Configure Traefik via command flags (no external config files): Docker provider, `rid-network`, entrypoints on :80 and :443
- Define forwardAuth middleware `rid-auth` pointing to `http://backend:8000/internal/auth-check/` with `trustForwardHeader=true` and `authResponseHeaders=X-Auth-User,X-Auth-Tenant`
- Add Traefik labels to `langflow` service: router rule `PathPrefix('/flows')`, middleware `rid-auth@docker,langflow-ws@docker`, internal port 7860
- Add `langflow-ws` middleware for WebSocket `Connection` and `Upgrade` headers passthrough
- Remove `ports: - "7861:7860"` from `langflow` service (staging/production; keep under `local` profile if needed)
- Update `LANGFLOW_BASE_URL` to `http://langflow:7860` in `langflow` service environment
- Update `LANGFLOW_CORS_ORIGINS` to platform domain (`https://app.rid.example.com`)
- Add optional Traefik labels to `backend` service for public exposure (`!PathPrefix('/flows')`)
- Mount Docker socket read-only (`/var/run/docker.sock:ro`) and `./certs:/certs:ro` volume
- Update `.env.example` with `LANGFLOW_BASE_URL`, `LANGFLOW_CORS_ORIGINS`
- Create internal network `rid-network` if not already declared

**Excludes:**
- Django settings changes (T-002)
- Auth Check Endpoint implementation (T-003)
- Error page implementation (T-004)
- Frontend heartbeat (T-005)
- TLS certificate provisioning (operational concern — documented in runbook)

---

### Success Criteria

**Functional:**
- `curl -I http://localhost/flows/` returns 302 (redirect to login) when no session cookie is present
- Port 7861 is not bound on the host (`ss -tlnp | grep 7861` returns empty)
- `docker compose --profile langflow up` starts Traefik, backend, langflow without errors
- WebSocket upgrade request to `/flows/` succeeds end-to-end (after auth) — verifiable with `websocat`

**Technical:**
- Traefik image pinned to `traefik:v3.3.6` (no `latest`)
- `exposedByDefault=false` in Traefik command flags
- All routing and middleware configured via Docker labels (zero external config files)
- `docker.sock` mounted as `:ro`
- `langflow-ws` middleware sets `Connection: keep-alive, Upgrade` and `Upgrade: websocket`

**Quality:**
- `docker compose config` validates without errors
- `docker scout cves traefik:v3.3.6` run and result documented in PR description
- `.env.example` updated with all new/changed variables from this task

---

### User Value
Closes the unprotected port 7861 entry point. Users can no longer bypass the platform's authentication by accessing Langflow directly — every access goes through the RID identity perimeter.

### Technical Value
Establishes the infrastructure foundation that all other tasks depend on. Enables forwardAuth sub-request flow, WebSocket proxying, and tenant-aware routing.

### Technical Components (TRD)
- Component 1 — Container-native Edge Router
- Component 5 — Editor Interno (port removal)

---

### Dependencies

**Blocks:** T-002 (settings meaningless without proxy), T-003 (auth-check must be reachable from Traefik), T-004 (error page flow triggered by Traefik), T-005 (heartbeat endpoint routed via Traefik), T-006 (all integration tests require Traefik running)

**Requires:** None (first task)

**Optional:** TLS certificate files in `./certs/` for HTTPS in staging

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| Traefik service definition (docker-compose) | 1h | Command flags, volumes, network, profile |
| forwardAuth middleware labels on langflow | 1h | rid-auth, langflow-ws, router rule |
| Langflow port removal + env vars update | 0.5h | Remove 7861, update BASE_URL + CORS |
| Backend labels (optional public exposure) | 0.5h | Not path /flows |
| `.env.example` update | 0.25h | Document new variables |
| Smoke test / validation | 0.75h | docker compose config, curl, port check |

**Total: 4h — Confidence: High** (well-specified in gate-6-dependency-map.md §8; exact YAML provided)

---

### Testing Strategy

- `docker compose config` — validates YAML syntax and variable interpolation
- `docker compose --profile langflow up -d` + `curl -I http://localhost/flows/` — verifies forwardAuth redirect
- `ss -tlnp | grep 7861` — verifies port removal
- `docker inspect rid-traefik` — verifies read-only socket mount
- Manual WebSocket test with `websocat` or browser DevTools

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `rid-network` not yet declared in docker-compose | Low | Medium | Create network declaration in this task; verify existing network name first |
| Langflow hash-based routing loses `#fragment` in `next` param | Medium | Low | Accepted MVP limitation; document in runbook (TRD §7.1) |
| CVE-2026-33186 or GHSA advisories affect v3.3.6 | Low | High | Run `docker scout cves traefik:v3.3.6` before deploy; pin to v3.3.7 if patch available |
| WebSocket timeout too short for long editor sessions | Low | High | Configure `responseHeaderTimeout` on backend service if needed; document recommended value |

---

### Definition of Done

- [ ] `traefik:v3.3.6` service added to `docker-compose.yml` under `langflow` profile
- [ ] forwardAuth middleware `rid-auth` defined with correct `address`, `trustForwardHeader=true`, `authResponseHeaders`
- [ ] `langflow-ws` WebSocket headers middleware defined and applied
- [ ] `ports: - "7861:7860"` removed from `langflow` service (guarded to `local` profile or removed entirely)
- [ ] `LANGFLOW_BASE_URL=http://langflow:7860` and `LANGFLOW_CORS_ORIGINS` updated
- [ ] `.env.example` updated with new/changed variables
- [ ] `docker compose config` passes without errors
- [ ] `curl -I http://localhost/flows/` returns 302 with no session cookie
- [ ] `ss -tlnp | grep 7861` is empty
- [ ] CVE check result documented in PR description

---

## T-002 — Django proxy header settings

**Target:** backend  
**Working Directory:** `/home/RID`  
**Agent:** `ring:backend-engineer-python`  
**Size:** S (2h)

**Deliverable:** Django correctly trusts and processes Traefik proxy headers — tenant resolution via `X-Forwarded-Host` works, secure cookies are enforced in staging/production, and ALLOWED_HOSTS covers both the public domain and the internal `backend` hostname used by Traefik forwardAuth sub-requests.

---

### Scope

**Includes:**
- Add `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` to Django settings
- Add `USE_X_FORWARDED_HOST = True` to Django settings (required for `TenantMainMiddleware` tenant resolution via forwarded host — TRD §7.4)
- Add `SESSION_COOKIE_SECURE = True` for production/staging (env-gated)
- Add `SESSION_COOKIE_SAMESITE = 'Lax'` for CSRF protection without breaking redirect flows
- Add `CSRF_COOKIE_SECURE = True` for production/staging (env-gated)
- Update `ALLOWED_HOSTS` to include `backend` (for Traefik internal sub-requests) and production domain
- Update `.env.example` with all new variables: `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECURE_PROXY_SSL_HEADER`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`

**Excludes:**
- Auth Check Endpoint view (T-003)
- Any Traefik configuration (T-001)
- Frontend changes (T-005)

---

### Success Criteria

**Functional:**
- Django `request.is_secure()` returns `True` when `X-Forwarded-Proto: https` header is present
- `connection.get_tenant()` resolves correct tenant when `X-Forwarded-Host` contains the tenant subdomain
- Session cookie is `Secure` flag set in staging/production responses (`Set-Cookie: ... Secure`)
- Django accepts requests with `Host: backend` (internal forwardAuth sub-requests from Traefik)

**Technical:**
- All new settings are env-gated (not hardcoded): read from `os.environ` or `django-environ`
- `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are `False` in local dev (no HTTPS required locally)
- No existing tests broken by header changes

**Quality:**
- `.env.example` updated with all new variables and inline comments explaining each setting
- Settings change reviewed for impact on existing session behavior (no regression in login flow)

---

### User Value
Ensures the platform correctly identifies which tenant a user belongs to when behind the proxy, and that session cookies are transmitted securely — a prerequisite for the auth perimeter to work correctly.

### Technical Value
Unblocks T-003 (auth-check relies on correct tenant resolution) and T-005 (heartbeat relies on session cookies being sent correctly). Without `USE_X_FORWARDED_HOST`, `TenantMainMiddleware` would resolve `backend` as the tenant hostname and fail.

### Technical Components (TRD)
- Component 3 — Django Settings for Proxy Headers

---

### Dependencies

**Blocks:** T-003 (tenant resolution in auth-check requires `USE_X_FORWARDED_HOST`), T-005 (secure session cookies required for heartbeat to work)

**Requires:** T-001 (Traefik must be running to validate forwarded headers end-to-end; settings can be coded independently but not fully tested without T-001)

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| Add settings to Django settings file | 0.5h | 6 settings, env-gated |
| Update ALLOWED_HOSTS logic | 0.25h | Add `backend` and prod domain |
| Update `.env.example` | 0.25h | Document each new variable |
| Unit test: `request.is_secure()` with mock header | 0.5h | Django `RequestFactory` |
| Manual smoke test with Traefik running | 0.5h | Requires T-001 |

**Total: 2h — Confidence: High** (exact settings listed in gate-6-dependency-map.md §3.1; no ambiguity)

---

### Testing Strategy

- Django unit test with `RequestFactory`: set `HTTP_X_FORWARDED_PROTO=https`, assert `request.is_secure() == True`
- Django unit test: set `HTTP_X_FORWARDED_HOST=tenant1.rid.example.com`, assert `TenantMainMiddleware` resolves correct tenant
- Integration test (with T-001): `curl -H "X-Forwarded-Proto: https"` verifies SSL header trusted
- Check `Set-Cookie` response header in staging for `Secure` flag

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `USE_X_FORWARDED_HOST=True` with untrusted proxy in local dev | Low | Medium | Only Traefik (known trusted proxy) sets this header in staging/prod; local dev has no proxy |
| Existing tests rely on `request.is_secure() == False` | Low | Low | Audit test suite before merging; fix affected tests |

---

### Definition of Done

- [ ] `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SECURE` added to Django settings (env-gated)
- [ ] `ALLOWED_HOSTS` updated to include `backend` and production domain
- [ ] `.env.example` updated with all 4 new env variables and inline comments
- [ ] Unit test: `request.is_secure()` with `X-Forwarded-Proto: https` passes
- [ ] Unit test: `TenantMainMiddleware` resolves tenant from `X-Forwarded-Host` passes
- [ ] No existing test regressions

---

## T-003 — Auth Check Endpoint

**Target:** backend  
**Working Directory:** `/home/RID`  
**Agent:** `ring:backend-engineer-python`  
**Size:** M (5h)

**Deliverable:** `GET /internal/auth-check/` is live in Django — returning 200 (valid session + correct tenant), 401 (absent/expired session), or 403 (tenant mismatch) — with async fire-and-forget audit logging on 200, `next` parameter validation, and p95 latency < 20ms.

---

### Scope

**Includes:**
- Django view at `GET /internal/auth-check/` with response contract: 200 / 401 / 403 (no body, status code only — TRD Component 2)
- Session validation: read Django session from request, verify active (not expired, not invalidated)
- Tenant validation: read active tenant from `django-tenants` middleware context (`connection.tenant`), compare against request's resolved tenant
- Audit logging on 200: async fire-and-forget write to platform audit system — fields: tenant, user, timestamp, original request URL (from `X-Forwarded-Uri` header if present)
- `next` parameter validation helper: `is_safe_next_url()` — accepts only internal paths (starts with `/`, not `//`, no `://`) — TRD §3.3 (used by redirect logic)
- URL route: `path('internal/auth-check/', ...)` in `urls.py` — accessible without CSRF (GET, read-only)
- Accessible to both Traefik sub-requests (internal network) AND browser heartbeat polling (same domain via Traefik)
- Performance: stateless read — no heavy I/O in hot path (session from Redis cache)

**Excludes:**
- Traefik configuration (T-001)
- Django proxy settings (T-002) — must be done first
- Frontend heartbeat (T-005)
- Error page (T-004)
- FastAPI / Async API Runtime — no session validation duplicated there (TRD §7.2)

---

### Success Criteria

**Functional:**
- `GET /internal/auth-check/` with valid session cookie + correct tenant → 200 (no body)
- `GET /internal/auth-check/` with no session cookie → 401 (no body)
- `GET /internal/auth-check/` with expired session → 401 (no body)
- `GET /internal/auth-check/` with valid session but wrong tenant → 403 (no body)
- `GET /internal/auth-check/` from Traefik forwardAuth sub-request (Host: backend) → resolves tenant correctly (requires T-002)
- Audit event written after 200 response; audit failure does NOT block the 200 response

**Technical:**
- Response body is empty (Traefik forwardAuth only cares about status code)
- `is_safe_next_url()` rejects: `//evil.com`, `https://evil.com`, `javascript:`, relative paths without leading `/`
- Session read from existing Redis session backend — no new I/O layer
- Audit write is async (Django async view or `threading.Thread` fire-and-forget)
- No CSRF token required (GET, idempotent, read-only)

**Quality:**
- p95 latency < 20ms measured in load test (50 req/s for 30s) — TRD §8
- Unit test coverage: all 4 response codes + `is_safe_next_url()` edge cases
- No duplication of `TenantMainMiddleware` resolution logic

---

### User Value
Makes authenticated access to the editor possible. Without this endpoint, Traefik cannot grant access to any user — the auth perimeter is non-functional.

### Technical Value
Central validation point for the entire feature. Provides 200/401/403 contract consumed by Traefik (infrastructure) and the React heartbeat (frontend). Enables audit trail (RF-005) and tenant isolation (RF-004).

### Technical Components (TRD)
- Component 2 — Auth Check Endpoint

---

### Dependencies

**Blocks:** T-005 (heartbeat polls this endpoint), T-006 (all auth/tenant tests depend on this endpoint)

**Requires:** T-001 (Traefik calls this endpoint; needed for integration testing), T-002 (proxy headers required for correct tenant resolution in sub-requests)

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| Django view: session validation (200/401) | 1h | Read session, check active |
| Django view: tenant validation (403) | 0.75h | Read `connection.tenant`, compare |
| Async audit logging (fire-and-forget) | 0.75h | Write to platform audit system |
| `is_safe_next_url()` helper + unit tests | 0.5h | TRD §3.3 logic |
| URL route registration + CSRF exemption | 0.25h | `urls.py` update |
| Unit tests (all 4 codes + audit fire-and-forget) | 1.25h | Mock session, mock tenant, mock audit |
| Performance validation (p95 < 20ms) | 0.5h | locust or wrk quick test |

**Total: 5h — Confidence: High** (contract fully defined in TRD Component 2; no design ambiguity)

---

### Testing Strategy

- Unit tests with `RequestFactory`:
  - Valid session + correct tenant → assert response.status_code == 200
  - No session cookie → assert 401
  - Expired session → mock expired session → assert 401
  - Valid session + wrong tenant → mock tenant mismatch → assert 403
  - Audit write failure → assert 200 still returned (fire-and-forget verified)
- `is_safe_next_url()` unit tests: table-driven with valid/invalid inputs (TRD §3.3 examples)
- Integration test (with T-001 + T-002): Traefik forwardAuth sub-request with valid session → editor accessible
- Performance test: locust/wrk at 50 req/s; assert p95 < 20ms

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Audit system write blocks the 200 response | Medium | High | Implement as true fire-and-forget (thread or async); add timeout; test explicitly |
| `connection.tenant` not set in forwardAuth sub-request context | Medium | High | Requires T-002 (`USE_X_FORWARDED_HOST=True`) to be in place; verify with integration test |
| Auth check endpoint accessible without authentication from public internet | Low | High | Endpoint returns 401 for unauthenticated requests — safe by design; no sensitive data in response |

---

### Definition of Done

- [ ] `GET /internal/auth-check/` view implemented and registered in `urls.py`
- [ ] Returns 200 (valid session + correct tenant), 401 (no/expired session), 403 (tenant mismatch)
- [ ] Response body is empty in all cases
- [ ] `is_safe_next_url()` helper implemented with edge case coverage
- [ ] Audit logging on 200: async fire-and-forget, failure does not block response
- [ ] Unit tests: all 4 response codes pass
- [ ] Unit tests: `is_safe_next_url()` table-driven cases pass
- [ ] Performance test: p95 < 20ms at 50 req/s
- [ ] No CSRF token required (GET route)

---

## T-004 — Error Page Template + Django view

**Target:** backend  
**Working Directory:** `/home/RID`  
**Agent:** `ring:backend-engineer-python`  
**Size:** M (4h)

**Deliverable:** `/flows/error/` serves a branded RID HTML error page in pt-BR — independent of Langflow assets — with "Tentar novamente" CTA (checks `/flows/` availability before navigating) and "Voltar ao painel" link, fully compliant with WCAG 2.1 AA.

---

### Scope

**Includes:**
- Django view at `GET /flows/error/` serving the error page template
- HTML template: RID visual identity, message in pt-BR, no dependency on Langflow assets (self-contained CSS inline or platform stylesheet)
- CTA "Tentar novamente" (primary): JavaScript `fetch('/flows/')` — navigate only if response is 200; show loading state during attempt; show error feedback if unavailable
- CTA "Voltar ao painel" (secondary): anchor link to platform dashboard
- WCAG 2.1 AA: `role="main"`, `aria-label` on CTAs, contrast >= 4.5:1, touch targets >= 44×44px on mobile
- Response time < 200ms independent of Langflow state (served directly by Django — no upstream call)
- URL route: `path('flows/error/', ...)` in `urls.py`
- Traefik custom error page configuration — reference this URL in the `langflow` service Traefik labels for 5xx/timeout upstream errors

**Excludes:**
- Traefik service setup (T-001) — though Traefik labels for error page routing are added to `langflow` service labels in T-001 or coordinated with T-001
- Session expiry overlay (T-005) — different component, different trigger
- Auth check endpoint (T-003)

---

### Success Criteria

**Functional:**
- `GET /flows/error/` returns 200 with HTML body (no dependency on Langflow being up)
- "Tentar novamente" button calls `GET /flows/` via JavaScript; if 200 → navigates to `/flows/`; if non-200 → shows "Editor ainda indisponível" feedback without page reload
- "Tentar novamente" shows loading state during the `fetch()` call
- "Voltar ao painel" is a plain anchor link (not JavaScript-dependent)
- Page renders correctly with Langflow container stopped

**Technical:**
- No `<link>` or `<script>` tags pointing to Langflow domains or internal Langflow ports
- Django view returns response in < 200ms when Langflow is down (no upstream probe)
- Template uses platform CSS variables or inline styles — no external CSS framework

**Quality:**
- WCAG 2.1 AA verified: axe-core scan in automated test shows 0 critical violations
- Contrast ratio >= 4.5:1 for all text (verified with browser DevTools or Lighthouse)
- Touch targets >= 44×44px on mobile viewport (tested at 375px width)
- pt-BR copy reviewed for clarity: message + CTAs

---

### User Value
When the Langflow editor is down for maintenance or restart, users see a clear branded page with actionable recovery options instead of a generic Traefik/nginx 502 error — reducing support tickets (PRD RF-003).

### Technical Value
Decouples error handling from Langflow's asset availability. Page can be served immediately by Django regardless of editor state, meeting the < 200ms response target.

### Technical Components (TRD)
- Component 4 — Error Page Template

---

### Dependencies

**Blocks:** T-006 (unavailability test scenario requires this page)

**Requires:** T-001 (Traefik must be configured to route 5xx/timeout to this page — coordination needed on Traefik `errors` middleware labels; can be developed in parallel, integrated at T-001)

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| Django view + URL route | 0.5h | Simple template view |
| HTML template (structure + pt-BR copy) | 1h | RID identity, semantic HTML |
| CSS (inline or platform vars) + responsive/WCAG | 1h | 4.5:1 contrast, 44×44px targets |
| JavaScript: "Tentar novamente" fetch logic + loading state | 0.75h | Vanilla JS, no framework |
| Axe-core WCAG automated check | 0.5h | Playwright or jest-axe |
| Manual test (Langflow stopped) | 0.25h | Verify < 200ms, no Langflow assets |

**Total: 4h — Confidence: High** (requirements fully specified in TRD Component 4 and DD-003/DD-005)

---

### Testing Strategy

- Django test: `GET /flows/error/` with Langflow container stopped → 200 response, < 200ms
- JavaScript unit test (jsdom): "Tentar novamente" fetch mock → 200 case (navigates) + 503 case (shows feedback)
- WCAG automated: `jest-axe` or Playwright + axe-core → 0 critical violations
- Visual test: render at 375px (mobile) and 1280px (desktop) — verify layout, touch targets
- Manual: verify no network requests to Langflow domain/port in browser DevTools

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Traefik custom error page configuration complexity | Medium | Medium | Traefik `errors` middleware supports custom error pages via backend URL; test integration with T-001 |
| Platform CSS variables not available in standalone error page | Low | Low | Use inline styles as fallback; test with platform CSS loaded and without |

---

### Definition of Done

- [ ] `GET /flows/error/` Django view implemented and registered in `urls.py`
- [ ] HTML template: RID identity, pt-BR copy, no Langflow asset dependencies
- [ ] "Tentar novamente" CTA: fetch `/flows/`, navigate on 200, show feedback on non-200, loading state during fetch
- [ ] "Voltar ao painel" CTA: plain anchor link to dashboard
- [ ] `role="main"`, `aria-label` on CTAs present in HTML
- [ ] Contrast >= 4.5:1, touch targets >= 44×44px verified
- [ ] WCAG axe-core scan: 0 critical violations
- [ ] Django response time < 200ms with Langflow stopped (measured)
- [ ] No network requests to Langflow domain in browser DevTools

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
- `useSessionHeartbeat.ts` hook (extracted — dependency-map §5.3): `useEffect` + `setInterval` at 120s interval; `fetch('/internal/auth-check/', { credentials: 'same-origin' })`; calls `onSessionExpired()` callback on HTTP 401; network errors are silent (no overlay on transient failures); `clearInterval` cleanup on unmount
- `SessionExpiryOverlay.tsx` component: full-screen overlay rendered on top of editor content; message "Sessão expirada" in pt-BR; CTA "Entrar novamente" → `window.location.href = '/login/?next=/flows/'`; keyboard navigation (Tab, Enter, Escape to... no dismiss — user must re-authenticate); `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"` (WCAG 2.1 AA — DD-005)
- Inline styles or plain CSS (no external component library — DD-004)
- Integration into RID shell: mount `SessionExpiryOverlay` in the shell component wrapping the Langflow editor; heartbeat active only when editor is mounted
- Accessibility: focus trap inside overlay; first focusable element receives focus on open; screen reader announces immediately via `aria-live="assertive"`

**Excludes:**
- Auth Check Endpoint implementation (T-003) — must exist before this can be tested
- Backend proxy settings (T-002) — required for correct cookie behavior
- Traefik configuration (T-001) — required for `/internal/auth-check/` to be routable
- WebSocket session expiry detection (out of MVP scope — TRD §7.3 known limitation)
- Overlay dismissal without re-authentication (by design — security requirement)

---

### Success Criteria

**Functional:**
- Overlay appears within 120 seconds of session expiry (next heartbeat cycle)
- "Entrar novamente" CTA redirects to `/login/?next=/flows/`
- Heartbeat `setInterval` is cleared when component unmounts (verified: no network requests after unmount)
- Network errors during heartbeat do NOT trigger overlay (only HTTP 401 does)
- HTTP 403 does NOT trigger the overlay (wrong tenant — different handling)

**Technical:**
- Hook exported as `useSessionHeartbeat` from `useSessionHeartbeat.ts` (separate file — standard: hooks > 20 lines in own file)
- `credentials: 'same-origin'` on all fetch calls (session cookie sent)
- Component uses no npm dependencies beyond React 18
- No `useEffect` for data fetching concern (exception justified: heartbeat is infrastructure polling, not data — dependency-map §5.3)

**Quality:**
- `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"` present in rendered HTML
- Focus moves to overlay on open (focus trap)
- Keyboard: Tab cycles through overlay elements only; Enter activates CTA; Escape does not close (by design)
- axe-core scan: 0 critical WCAG violations on overlay
- Contrast >= 4.5:1 on overlay text
- Touch target of "Entrar novamente" >= 44×44px

---

### User Value
Users working in the editor for extended sessions are proactively warned before being abruptly redirected, allowing them to save work and re-authenticate without confusion (PRD RF-001, DD-001).

### Technical Value
Implements the client-side session expiry detection pattern (DD-001) that avoids relying on Traefik's 302 redirect during active WebSocket/browser use. Cancels cleanly on unmount, preventing memory leaks and ghost polling.

### Technical Components (TRD)
- Component 3 — Session Expiry Overlay (Frontend SPA)

---

### Dependencies

**Blocks:** T-006 (overlay scenario requires frontend component deployed)

**Requires:** T-001 (Traefik routes `/internal/auth-check/` to Django; required for integration testing), T-002 (secure session cookies required for heartbeat to carry session), T-003 (endpoint must exist and return 401)

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| `useSessionHeartbeat.ts` hook implementation | 1h | setInterval, fetch, cleanup, 401 detection |
| `SessionExpiryOverlay.tsx` component | 1.5h | Overlay UI, pt-BR copy, CTA |
| Inline styles / plain CSS for overlay | 0.5h | Full-screen, z-index, contrast |
| WCAG attributes + focus trap | 0.75h | role, aria-modal, aria-live, focus management |
| Shell integration (mount point) | 0.5h | Wrap editor route in shell |
| Unit tests (hook + component) | 0.75h | Mock fetch, mock timers, jest |

**Total: 5h — Confidence: High** (implementation pattern fully specified in dependency-map §5.1–5.3)

---

### Testing Strategy

- Hook unit test (jest + `@testing-library/react-hooks`):
  - Mock `fetch` to return 401 → assert `onSessionExpired` called after interval tick
  - Mock `fetch` to throw network error → assert `onSessionExpired` NOT called
  - Unmount → assert `clearInterval` called (no pending timers)
- Component unit test (`@testing-library/react`):
  - Render overlay → assert `role="alertdialog"`, `aria-modal`, `aria-live` in DOM
  - Click "Entrar novamente" → assert `window.location.href` change
  - axe-core check: 0 critical violations
- Integration test (with T-001 + T-003): let session expire in test environment → assert overlay appears within 2 heartbeat cycles

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Traefik returns 302 instead of 401 for heartbeat request | Low | High | Heartbeat uses `fetch()` with `redirect: 'manual'` — 302 is treated as opaque response, not 401; verify with T-003 that direct browser requests to `/internal/auth-check/` return 401 (Traefik only redirects navigation, not XHR/fetch sub-requests) |
| Focus trap breaks existing editor keyboard navigation | Low | Medium | Focus trap is scoped to overlay only; deactivated when overlay is not mounted |
| Multiple heartbeat intervals created (StrictMode double-invoke) | Low | Low | Cleanup function in `useEffect` ensures only one interval active; test with StrictMode enabled |

---

### Definition of Done

- [ ] `useSessionHeartbeat.ts` hook implemented in separate file
- [ ] `credentials: 'same-origin'` on fetch; 120s interval; `clearInterval` on unmount
- [ ] Only HTTP 401 triggers overlay (network errors and 403 are silent)
- [ ] `SessionExpiryOverlay.tsx` component: pt-BR copy, "Entrar novamente" CTA → `/login/?next=/flows/`
- [ ] `role="alertdialog"`, `aria-modal="true"`, `aria-live="assertive"` in rendered HTML
- [ ] Focus trap active while overlay is mounted; focus moves to overlay on open
- [ ] No npm dependencies added
- [ ] Hook unit tests pass (401 trigger, error silence, cleanup)
- [ ] Component unit tests pass (ARIA attrs, CTA behavior)
- [ ] axe-core: 0 critical violations on overlay
- [ ] Contrast >= 4.5:1, touch target >= 44×44px verified

---

## T-006 — Integration + E2E tests

**Target:** shared/qa  
**Working Directory:** `/home/RID`  
**Agent:** `ring:qa-analyst`  
**Size:** M (6h)

**Deliverable:** A complete integration and E2E test suite covering all security and user experience scenarios for the auth perimeter: unauthenticated access, authenticated access, session expiry overlay, editor unavailability error page, tenant isolation (cross-tenant 403), and WebSocket upgrade through forwardAuth.

---

### Scope

**Includes:**
- **Scenario 1 — Unauthenticated access → redirect to login:** `GET /flows/` without session cookie → assert HTTP 302 with `Location: /login/?next=%2Fflows%2F`
- **Scenario 2 — Authenticated access → editor loads:** `GET /flows/` with valid session cookie + correct tenant → assert 200 and Langflow HTML in response
- **Scenario 3 — Session expiry → overlay appears:** authenticated user in editor → expire session server-side → wait for next heartbeat (120s or mock timer) → assert overlay element visible in DOM with correct ARIA attributes
- **Scenario 4 — Langflow unavailable → error page shown:** stop Langflow container → `GET /flows/` with valid session → assert Django error page at `/flows/error/` returned (not generic 502)
- **Scenario 5 — Tenant isolation → 403 for wrong tenant:** authenticated user from tenant A → request `/flows/` with `Host` header of tenant B → assert 403 response
- **Scenario 6 — WebSocket upgrade through forwardAuth:** authenticated session → WebSocket connect to `/flows/` → assert upgrade succeeds (101 Switching Protocols)
- **Scenario 7 — Port 7861 not publicly accessible:** assert `curl http://localhost:7861` connection refused (or no response)
- `is_safe_next_url()` unit tests (integrated from T-003 or run here): table-driven edge cases
- `.env.example` completeness check: assert all variables documented in dependency-map §3.2 and §4.x are present

**Excludes:**
- WCAG testing (covered in T-004 and T-005)
- Performance load testing of Auth Check Endpoint (covered in T-003)
- Langflow editor functionality testing (out of scope — Langflow not modified)
- TLS certificate validation in CI (use HTTP in test environment)

---

### Success Criteria

**Functional (all 7 scenarios pass):**
- Scenario 1: 302 with correct `Location` header and encoded `next` param
- Scenario 2: 200 with Langflow HTML (not auth-check body)
- Scenario 3: overlay DOM element with `role="alertdialog"` visible after session expiry + heartbeat tick
- Scenario 4: error page HTML returned by Django (contains RID branding, CTAs) — not Traefik 502 HTML
- Scenario 5: 403 response for cross-tenant access
- Scenario 6: WebSocket 101 Switching Protocols
- Scenario 7: `curl http://localhost:7861` fails (connection refused)

**Technical:**
- Tests run in CI via `docker compose --profile langflow` (full stack)
- Test environment uses HTTP (no TLS certificates required in CI)
- Scenarios 1, 2, 4, 5, 7 implemented as Pytest + `httpx` integration tests against running stack
- Scenario 3 implemented as Playwright E2E test (browser required for JavaScript heartbeat)
- Scenario 6 implemented as `websockets` Python client test
- Test isolation: each test uses unique session fixture; tenants created/cleaned per test

**Quality:**
- All 7 scenarios pass on clean `docker compose up` (no pre-existing state required)
- Test suite completes in < 5 minutes in CI
- Flaky test rate: 0 (no timing-dependent tests without explicit mocks)

---

### User Value
Provides automated regression protection for the entire auth perimeter. Ensures no future change breaks security invariants: unauthenticated access blocked, tenant isolation enforced, error page shown on failure.

### Technical Value
Validates the integration between all 5 TRD components in a running environment. Serves as executable documentation of the feature's security contract.

### Technical Components (TRD)
- All 5 components (integration validation)

---

### Dependencies

**Blocks:** None (final task)

**Requires:** T-001 (Traefik running), T-002 (proxy headers), T-003 (auth-check endpoint), T-004 (error page), T-005 (overlay component)

---

### Effort Estimate

| Sub-item | Est. | Notes |
|----------|------|-------|
| CI docker-compose test environment setup | 0.5h | `--profile langflow`, HTTP mode |
| Scenarios 1 + 2 (httpx: unauth + auth access) | 0.75h | Straightforward HTTP assertions |
| Scenario 3 (Playwright: session expiry overlay) | 1.25h | Browser test, timer mocking |
| Scenario 4 (httpx: Langflow stopped → error page) | 0.75h | Stop container, assert Django response |
| Scenario 5 (httpx: cross-tenant 403) | 0.75h | Tenant fixture setup |
| Scenario 6 (websockets client: WebSocket upgrade) | 0.5h | 101 assertion |
| Scenario 7 (port 7861 not bound) | 0.25h | Simple socket check |
| `.env.example` completeness check | 0.25h | Script or fixture |

**Total: 6h — Confidence: Medium** (scenarios are well-defined; medium confidence due to test environment setup variability with docker-compose in CI and Playwright timing for session expiry overlay)

---

### Testing Strategy

This task IS the testing strategy. Key implementation notes:

- Use `pytest-docker` or `docker compose` CLI to manage container lifecycle in tests
- Scenario 3 (session expiry): use Playwright's `page.clock.tick(120_000)` to advance timer without real wait
- Scenario 4 (unavailability): use `docker compose stop langflow` before the test, `start` after
- Scenario 5 (tenant isolation): requires two tenant fixtures; use `django-tenants` test utilities
- Scenario 6 (WebSocket): use `websockets` Python library; assert `101` on handshake

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Playwright timer advancement for session expiry flaky in CI | Medium | Medium | Use `page.clock.install()` + `tick()` to deterministically advance JS timers; avoid `sleep()` |
| Cross-tenant test fixture setup complexity | Medium | Medium | Use existing `django-tenants` test utilities; create minimal tenant fixtures |
| `docker compose stop langflow` race condition in unavailability test | Low | Low | Add health check assertion before and after stop; use `docker compose wait` |
| WebSocket upgrade test fails due to Traefik version-specific header handling | Low | Medium | Pin to v3.3.6 in CI; verify `Upgrade` and `Connection` headers explicitly |

---

### Definition of Done

- [ ] All 7 scenarios implemented as automated tests
- [ ] Tests pass on clean `docker compose --profile langflow up` in CI
- [ ] Scenario 3 uses timer mocking (not real 120s wait)
- [ ] Test suite completes in < 5 minutes
- [ ] No flaky tests (0 random failures over 3 consecutive CI runs)
- [ ] `.env.example` completeness verified by test or checklist
- [ ] Test results documented in PR (pass/fail per scenario)

---

## Dependency graph

```
T-001 (Traefik + docker-compose)
  │
  ├── T-002 (Django proxy settings)
  │     │
  │     └── T-003 (Auth Check Endpoint)
  │           │
  │           └── T-005 (Session Expiry Overlay)
  │                 │
  │                 └── T-006 (Integration + E2E tests)
  │                       ▲
  ├── T-004 (Error Page) ──┘
  │
  └─────────────────────────────────┘ (T-001 also required for T-006)
```

**Parallelism opportunities:**
- T-002 and T-004 can run in parallel after T-001
- T-005 can begin implementation in parallel with T-003 (mock the endpoint locally); full integration test requires T-003
- T-006 requires all previous tasks to be merged

---

## Feature coverage

| RF / Feature | Covered by |
|-------------|-----------|
| RF-001 Perímetro de autenticação | T-001, T-003, T-006 (Scenarios 1, 2) |
| RF-002 Endereço único e estável | T-001 (PathPrefix routing), T-006 (Scenario 6 WebSocket) |
| RF-003 Página de indisponibilidade | T-004, T-006 (Scenario 4) |
| RF-004 Isolamento por tenant | T-003 (403 logic), T-006 (Scenario 5) |
| RF-005 Auditoria de acesso | T-003 (fire-and-forget audit write) |
| DD-001 Sessão expirada via overlay | T-005, T-006 (Scenario 3) |
| DD-002 HTTP 302 directo | T-001 (Traefik forwardAuth behavior), T-006 (Scenario 1) |
| DD-003 Página de erro dois CTAs | T-004 |
| DD-004 React 18 nativo sem library | T-005 |
| DD-005 WCAG 2.1 AA | T-004, T-005 |
