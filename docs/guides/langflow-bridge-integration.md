# Integração com a bridge Langflow

Este guia explica como o frontend obtém credenciais Langflow através do backend RID, usando a sessão Django autenticada. A bridge segue a **Opção C (service-user)**: o browser recebe o JWT e a API key do **utilizador de serviço do tenant** (`rid.svc.<schema>@tenant.rid`), mais o `workspace_id` do project Langflow do tenant.

## Pré-requisitos

- Utilizador autenticado no RID (sessão com cookie).
- `TenantMembership` activo para o tenant em causa.
- `Customer.langflow_workspace_id` já provisionado (via `provision_tenant_langflow_project`); caso contrário a bridge responde `409`.
- `LANGFLOW_BASE_URL` e `LANGFLOW_SUPERUSER_API_KEY` configurados no backend quando a integração Langflow estiver activa.
- CORS configurado para o origin do frontend em desenvolvimento (ver `CORSMiddleware` em `api/main.py`).

## Fluxo resumido

1. O utilizador inicia sessão no RID (Django).
2. O frontend chama `GET /api/v1/langflow/auth/auto-login` com `credentials: 'include'` e o cabeçalho `Host` que corresponde ao domínio do tenant (ou, em alternativa, o query param `tenant_schema` — ver abaixo).
3. O backend valida a sessão, confirma membership, resolve o `Customer`, obtém JWT + API key do utilizador de serviço Langflow (com cache da key em `Customer.langflow_service_api_key`) e devolve `access_token`, `api_key` e `workspace_id`.
4. O frontend usa `workspace_id` no embed Langflow (project/Folder do tenant) e as credenciais conforme a API Langflow (`x-api-key` e/ou Bearer).

Implementação: `api/routers/langflow_auth.py`, `api/services/langflow_client.py` (`get_tenant_service_credentials`), provisionamento: `api/services/langflow_workspace.py`. Ver [ADR-009](../adr/ADR-009-langflow-database-integration.md).

## Chamada desde o browser

Use o mesmo origin que o backend espera para CORS, e inclua credenciais:

```javascript
const res = await fetch(`${API_BASE}/api/v1/langflow/auth/auto-login`, {
  method: 'GET',
  credentials: 'include',
  headers: { Accept: 'application/json' },
});
if (!res.ok) throw new Error(`auto-login failed: ${res.status}`);
const { access_token, api_key, workspace_id, langflow_user_id } = await res.json();
```

**Notas:**

- **`API_BASE`**: URL do backend RID (por exemplo `http://localhost:8000`). Não confundir com `LANGFLOW_BASE_URL` (servidor Langflow, tipicamente `http://localhost:7861` no compose).
- Nos browsers, o cabeçalho **`Host` é definido automaticamente** pelo runtime a partir do hostname de `API_BASE` — não é possível (nem seguro) forçá-lo em `fetch`. Para a bridge resolver o tenant pelo domínio, o utilizador deve aceder ao backend **no hostname do tenant** (ex.: `https://acme.rid.localhost` com o mesmo API atrás de um reverse proxy que preserve o host), **ou** usar sempre `?tenant_schema=...` quando o API estiver num host partilhado (ex.: `localhost:8000`).
- **`langflow_user_id`** na resposta está **deprecated** e vem `null` neste fluxo; não depender dele.

### Vários tenants por utilizador

Se o utilizador tiver **mais do que um** `TenantMembership` activo, é **obrigatório** passar o schema explícito:

```text
GET /api/v1/langflow/auth/auto-login?tenant_schema=<schema_name>
```

O backend valida que o utilizador é membro desse schema. O cabeçalho `Host` pode ser genérico (ex.: `localhost`) neste modo, desde que a sessão seja válida.

Referência HTTP completa: [Langflow bridge — referência de API](../api/langflow-bridge.md).

## Variáveis de ambiente relevantes

| Variável | Papel |
|----------|--------|
| `LANGFLOW_BASE_URL` | URL base do serviço Langflow (o backend usa-a para login e API keys). |
| `LANGFLOW_SUPERUSER_API_KEY` | Chave de superuser: criação de utilizadores e projects na fase de provisionamento (`provision_tenant_langflow_project`). |
| `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` | Credenciais do superuser Langflow em ambientes que as usem (ex.: compose de desenvolvimento). |

Lista completa: `backend/.env.example`.

## Ver também

- [ADR-009 — Integração Langflow com PostgreSQL](../adr/ADR-009-langflow-database-integration.md)
- [Implantação Langflow e tenants](../operations/langflow-deployment-and-tenants.md)
