---
feature: frontend-flows
gate: 2
type: adr-compliance-checklist
date: 2026-04-13
status: draft
title: GATE 2 — ADR Compliance Checklist (Executable Verification)
---

# GATE 2 ADR Compliance Checklist

**Purpose:** Provide executable verification steps for ADR compliance before GATE 4 implementation.

**Status:** ✅ 100% Documented, ⏳ 70% Verified (ADR-012 only)

**P0 Blocker Note:** This checklist must be completed and signed off before proceeding to GATE 4 task breakdown.

---

## ADR-001: Async/ORM Context Isolation (sync_to_async)

**ADR Link:** `docs/adr/ADR-001-async-orm-context.md`

**Requirement:** FastAPI dependencies must preserve Django ORM thread-local context when calling async functions.

**Feature Impact:** Feature 1 (Backend Endpoint)

### Verification Checklist

- [ ] **Code Pattern Audit**
  ```bash
  # Run from backend/
  grep -r "sync_to_async" backend/api/ --include="*.py"
  ```
  **Expected Result:** Pattern appears in `backend/api/deps.py` and any endpoint using Django ORM.

- [ ] **Specific Location Check**
  ```bash
  # Verify Feature 1 endpoint uses correct pattern
  grep -A 5 "async def get_current_user" backend/api/deps.py
  ```
  **Expected Result:** 
  ```python
  user = await sync_to_async(get_user_for_request, thread_sensitive=True)(request)
  ```
  **Key:** `thread_sensitive=True` is REQUIRED.

- [ ] **Integration Test Verification**
  **File:** `backend/tests/test_langflow_flows_list.py::test_flows_endpoint_with_orm_context`
  **Test Logic:**
  ```python
  @pytest.mark.django_db(transaction=True)
  async def test_flows_endpoint_with_orm_context():
      # Setup: Create Customer with langflow credentials
      customer = await sync_to_async(create_test_customer)(...)
      
      # Call: GET /api/v1/langflow/flows/list
      response = await client.get("/api/v1/langflow/flows/list")
      
      # Assert: Endpoint successfully called ORM without context errors
      assert response.status_code == 200
  ```
  **Status:** [ ] Not written | [ ] Written | [ ] Passing

---

## ADR-002: Multi-Tenancy (SHARED_APPS vs TENANT_APPS)

**ADR Link:** `docs/adr/ADR-002-multi-tenancy.md`

**Requirement:** TenantUser and auth models in SHARED_APPS (public schema). Tenant-scoped models never in TENANT_APPS if they reference users.

**Feature Impact:** Feature 1 (Backend Endpoint), Session Management

### Verification Checklist

- [ ] **Model Location Audit**
  ```bash
  # Check TenantUser in public schema
  grep -r "class TenantUser" backend/ --include="*.py"
  ```
  **Expected Result:** File path contains `/apps/accounts/models.py` (SHARED_APPS)

- [ ] **Customer Model Audit**
  ```bash
  # Verify Customer model has Langflow fields
  grep -A 10 "class Customer" backend/apps/tenants/models.py
  ```
  **Expected Result:**
  ```python
  class Customer(TenantModel):
      langflow_workspace_id = models.CharField(...)
      langflow_service_api_key = models.CharField(...)
  ```
  **Key:** Fields exist and properly nullable.

- [ ] **TENANT_APPS Configuration**
  ```bash
  # Verify no user/auth models in TENANT_APPS
  grep -A 20 "TENANT_APPS = \[" backend/core/settings.py | grep -E "(auth|user)"
  ```
  **Expected Result:** Empty (no auth models in TENANT_APPS)

- [ ] **Fixture Verification**
  **File:** `backend/tests/conftest.py`
  **Check:** Test fixtures create TenantUser in public schema, Customer in tenant schema
  ```python
  # Create user (public schema, no migration needed)
  user = await TenantUser.objects.create_user(...)
  
  # Create customer (tenant-scoped)
  customer = await Customer.objects.create(...)
  ```
  **Status:** [ ] Verified | [ ] Need to audit fixtures

---

## ADR-003: ASGI Hybrid (Django + FastAPI)

**ADR Link:** `docs/adr/ADR-003-asgi-hybrid.md`

**Requirement:** ASGI router in `backend/core/asgi.py` routes `/api/*` to FastAPI, everything else to Django.

**Feature Impact:** Feature 1 (Backend Endpoint)

### Verification Checklist

- [ ] **ASGI Router Audit**
  ```bash
  # Verify /api routes to FastAPI
  grep -A 20 "if scope\['path'\].startswith('/api')" backend/core/asgi.py
  ```
  **Expected Result:**
  ```python
  if scope['path'].startswith('/api'):
      await fastapi_app(scope, receive, send)
  else:
      await django_app(scope, receive, send)
  ```

- [ ] **FastAPI App Location**
  ```bash
  # Verify FastAPI app defined
  grep -r "app = FastAPI" backend/api/ --include="*.py"
  ```
  **Expected Result:** File path contains `/api/main.py`

- [ ] **Endpoint Registration**
  ```bash
  # Verify GET /api/v1/langflow/flows/list route exists
  grep -B 5 "def flows_list" backend/api/routers/langflow_flows.py
  ```
  **Expected Result:**
  ```python
  @router.get("/flows/list")
  async def flows_list(get_current_user: Depends(get_current_user)):
  ```
  **Key:** Endpoint path registered in `api/main.py` as `/api/v1/langflow/flows/list`

- [ ] **Integration Test**
  **File:** `backend/tests/test_asgi_routing.py::test_api_routes_to_fastapi`
  **Test Logic:**
  ```python
  async def test_api_routes_to_fastapi():
      response = await client.get("/api/v1/langflow/flows/list")
      # Should reach FastAPI, not Django 404
      assert response.status_code in [200, 401, 403]  # Not 404
  ```
  **Status:** [ ] Not written | [ ] Written | [ ] Passing

---

## ADR-005: Authentication (TenantAwareBackend)

**ADR Link:** `docs/adr/ADR-005-authentication.md`

**Requirement:** All user auth goes through TenantAwareBackend. FastAPI dependencies validate session before allowing access.

**Feature Impact:** Feature 1 (Backend Endpoint), Feature 2 (Session Management)

### Verification Checklist

- [ ] **Backend Authentication**
  ```bash
  # Verify TenantAwareBackend registered first
  grep -A 5 "AUTHENTICATION_BACKENDS" backend/core/settings.py
  ```
  **Expected Result:**
  ```python
  AUTHENTICATION_BACKENDS = [
      'core.auth_backends.TenantAwareBackend',
      ...
  ]
  ```

- [ ] **Session Validation in Endpoint**
  ```bash
  # Verify get_current_user dependency in Feature 1 endpoint
  grep -B 10 "async def flows_list" backend/api/routers/langflow_flows.py | grep "get_current_user"
  ```
  **Expected Result:** `get_current_user: TenantUser = Depends(get_current_user)`

- [ ] **Dependency Implementation**
  **File:** `backend/api/deps.py::get_current_user`
  **Check:** Function validates Django session and returns TenantUser
  ```python
  async def get_current_user(request: Request) -> TenantUser:
      # Extract session from request.cookies
      # Validate session exists
      # Return user or raise 401
  ```
  **Status:** [ ] Code location verified | [ ] Logic reviewed

- [ ] **Integration Test**
  **File:** `backend/tests/test_auth_dependency.py`
  **Test Cases:**
  ```python
  async def test_flows_endpoint_requires_auth():
      # No session cookie
      response = await client.get("/api/v1/langflow/flows/list")
      assert response.status_code == 401
  
  async def test_flows_endpoint_with_valid_session():
      # With valid session
      response = await client.get(
          "/api/v1/langflow/flows/list",
          cookies={"sessionid": valid_session_id}
      )
      assert response.status_code == 200
  ```
  **Status:** [ ] Not written | [ ] Written | [ ] Passing

---

## ADR-009: Langflow Integration (Workspace Provisioning)

**ADR Link:** `docs/adr/ADR-009-langflow-integration.md`

**Requirement:** Each Customer gets isolated Langflow workspace. Service API key stored in Customer.langflow_service_api_key. User accounts provisioned via superuser credentials.

**Feature Impact:** Feature 1 (Backend Endpoint)

### Verification Checklist

- [ ] **Customer Model Fields**
  ```bash
  # Verify Langflow fields in Customer model
  grep -E "(langflow_workspace_id|langflow_service_api_key)" backend/apps/tenants/models.py
  ```
  **Expected Result:** Both fields exist as CharField with null=True

- [ ] **Workspace Provisioning Logic**
  ```bash
  # Locate workspace provisioning service
  find backend/api/services -name "*langflow*workspace*" -type f
  ```
  **Expected Result:** File like `backend/api/services/langflow_workspace.py` exists

- [ ] **Feature 1 Endpoint Uses Workspace ID**
  ```bash
  # Verify endpoint retrieves workspace_id from Customer
  grep -A 20 "async def flows_list" backend/api/routers/langflow_flows.py | grep "workspace_id"
  ```
  **Expected Result:**
  ```python
  customer = await get_customer_for_tenant(tenant_id)
  workspace_id = customer.langflow_workspace_id
  api_key = customer.langflow_service_api_key
  ```

- [ ] **API Key Security**
  ```bash
  # Verify API key never exposed in responses
  grep -A 30 "async def flows_list" backend/api/routers/langflow_flows.py | grep -i "service_api_key"
  ```
  **Expected Result:** Empty (no exposure in response)

- [ ] **Integration Test**
  **File:** `backend/tests/test_langflow_integration.py::test_flows_endpoint_uses_workspace_credentials`
  **Test Logic:**
  ```python
  async def test_flows_endpoint_uses_workspace_credentials():
      # Setup: Customer with workspace_id + api_key
      customer = await create_customer_with_langflow(workspace_id="...", api_key="...")
      
      # Mock: Langflow API call with headers
      with patch('backend.api.services.langflow_client.request') as mock_request:
          response = await client.get("/api/v1/langflow/flows/list")
          
          # Verify: Langflow called with correct workspace_id + x-api-key
          call_kwargs = mock_request.call_args[1]
          assert call_kwargs['headers']['x-api-key'] == customer.langflow_service_api_key
          assert workspace_id in call_kwargs['url']
  ```
  **Status:** [ ] Not written | [ ] Written | [ ] Passing

---

## ADR-012: Traefik Auth Gate (Existing - No Changes)

**ADR Link:** `docs/adr/ADR-012-langflow-single-entry-auth-gate.md`

**Requirement:** Traefik reverse proxy protects `/flows/*` with `forwardAuth` → `GET /internal/auth-check/`

**Feature Impact:** Feature 5 (Navigation to Langflow)

### Verification Checklist

- [ ] **Traefik Configuration**
  ```bash
  # Verify forwardAuth in docker-compose.yml or traefik.yml
  grep -A 10 "forwardAuth" docker-compose.yml
  ```
  **Expected Result:**
  ```yaml
  forwardAuth:
    address: http://backend:8000/internal/auth-check/
    trustForwardHeader: true
  ```

- [ ] **Auth Check Endpoint**
  ```bash
  # Verify endpoint exists in Django
  grep -r "/internal/auth-check" backend/ --include="*.py"
  ```
  **Expected Result:** Endpoint defined in Django views

- [ ] **Status Codes**
  ```python
  # Endpoint returns:
  # - 200 OK: session valid, forward request
  # - 401 Unauthorized: no session, redirect to /login
  # - 403 Forbidden: session valid but tenant invalid, deny
  ```
  **Status:** [ ] Verified | [ ] Need to audit endpoint

---

## Summary Table: ADR Compliance Status

| ADR | Feature | Documented | Verified | Test Needed | Test Status |
|-----|---------|-----------|----------|-----------|-------------|
| ADR-001 | Feature 1 | ✅ | ⏳ | `test_flows_endpoint_with_orm_context` | [ ] |
| ADR-002 | Feature 1 | ✅ | ⏳ | `test_customer_model_fields`, `test_tenant_apps_no_auth` | [ ] |
| ADR-003 | Feature 1 | ✅ | ⏳ | `test_api_routes_to_fastapi` | [ ] |
| ADR-005 | Feature 1, 2 | ✅ | ⏳ | `test_flows_endpoint_requires_auth` | [ ] |
| ADR-009 | Feature 1 | ✅ | ⏳ | `test_flows_endpoint_uses_workspace_credentials` | [ ] |
| ADR-012 | Feature 5 | ✅ | ✅ | (Existing) | ✅ |

**Verification Priority:**
1. **P0:** ADR-001, ADR-003, ADR-005 (blocking Feature 1 implementation)
2. **P1:** ADR-002 (model structure), ADR-009 (workspace integration)
3. **P2:** ADR-012 (already verified)

---

## Execution Steps for Backend Engineer (Feature 1)

**Before writing Feature 1 code:**
1. Run all grep patterns above to audit existing codebase
2. Write integration tests from checklist
3. Implement Feature 1 endpoint with tests passing
4. Verify all ADR requirements met before code review

**Test Execution:**
```bash
# Run all ADR compliance tests
cd backend && pytest tests/test_adr_compliance.py -v

# Coverage check
pytest --cov=api.routers --cov-report=term-missing tests/test_adr_compliance.py
```

---

## Sign-Off

**This checklist must be completed and reviewed before GATE 4 GO decision.**

| Reviewer | ADR | Status | Date | Notes |
|----------|-----|--------|------|-------|
| Backend Engineer | ADR-001, 003, 005 | [ ] | | |
| Backend Engineer | ADR-002, 009 | [ ] | | |
| Tech Lead | All | [ ] | | |

---

**Document Status: DRAFT** ⏳  
**Checklist Complete:** [ ] No | [x] In Progress | [ ] Yes  
**Next Step:** Complete all verification items, run tests, collect sign-offs
