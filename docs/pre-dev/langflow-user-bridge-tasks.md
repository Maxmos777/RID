# Tasks — Bridge Django Auth → Langflow por utilizador

**Feature:** Autenticação por utilizador no Langflow após login Django  
**ADRs relevantes:** ADR-001, ADR-002, ADR-004, ADR-009  
**Stack:** Python 3.12, Django 6, FastAPI, httpx  

---

## Task 1 — Corrigir `langflow_client.py`: API Key + activação de utilizador

**Ficheiro:** `backend/api/services/langflow_client.py`

### Subtask 1.1 — RED: escrever testes que falham

```python
# test_langflow_client.py
# test_get_or_create_uses_api_key_not_password
# test_user_activated_after_creation
# test_langflow_user_id_returned
```

### Subtask 1.2 — GREEN: implementar

Alterar `_get_superuser_token()`:
- REMOVER login com username+password
- USAR `x-api-key: LANGFLOW_SUPERUSER_API_KEY` directamente nos headers

Alterar `get_or_create_langflow_user()`:
- `POST /api/v1/users/` com header `x-api-key`
- Se 201 (novo user): `PATCH /api/v1/users/{id}` com `{"is_active": True}` 
- Retornar `user_id` (UUID) além de `access_token` e `api_key`

### Subtask 1.3 — REFACTOR: retorno tipado

```python
# Retornar TypedDict ou dataclass em vez de dict genérico
class LangflowUserResult(TypedDict):
    access_token: str
    api_key: str
    user_id: str  # UUID do utilizador no Langflow
```

---

## Task 2 — Corrigir `langflow_auth.py`: guardar `langflow_user_id`

**Ficheiro:** `backend/api/routers/langflow_auth.py`

### Subtask 2.1 — Guardar `langflow_user_id` ao criar utilizador

```python
# Após get_or_create_langflow_user:
# user.langflow_user_id = UUID(result["user_id"])
# user.langflow_api_key = result["api_key"]
# user.save(update_fields=["langflow_user_id", "langflow_api_key"])
```

### Subtask 2.2 — Re-login usa API Key do user em cache

```python
# Se langflow_api_key presente: re-login directo para JWT fresco
# Sem chamar get_or_create (evita criação duplicada)
```

---

## Task 3 — Testes

**Ficheiro:** `backend/tests/test_langflow_client.py` (novo)  
**Actualizar:** `backend/tests/test_langflow_workspace.py`

Cenários obrigatórios:
1. `test_uses_api_key_header_not_password_login` 
2. `test_new_user_activated_after_creation`
3. `test_existing_user_skips_activation`
4. `test_user_id_saved_in_tenant_user`
5. `test_auto_login_returns_fresh_jwt_on_cache_hit`

---

## Critérios de Aceitação

- [ ] `_get_superuser_token()` removida ou refactored para usar API Key
- [ ] Novo utilizador Langflow criado com `is_active=True` após auto-login
- [ ] `TenantUser.langflow_user_id` preenchido após primeiro auto-login
- [ ] `TenantUser.langflow_api_key` preenchido após primeiro auto-login
- [ ] Re-login em utilizador existente não cria duplicado
- [ ] `ruff check .` sem erros
- [ ] `pytest -q` ≥ 36 testes passam (sem regressões)
