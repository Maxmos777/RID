# Langflow bridge — referência de API

Endpoints FastAPI expostos pelo backend RID para autenticação Langflow. A aplicação FastAPI está montada em `/api` no ASGI; os caminhos abaixo são **paths completos** a partir da raiz do host do backend (ex.: `https://api.exemplo.com/api/v1/langflow/...`).

## Autenticação

Os endpoints da bridge destinados ao browser assumem **sessão Django** (cookie de sessão). Não usam Bearer do RID neste fluxo.

---

## Obter credenciais Langflow (auto-login)

Obtém JWT e API key do **utilizador de serviço Langflow** do tenant, e o UUID do **workspace** (project Langflow) associado ao `Customer`.

### Request

```http
GET /api/v1/langflow/auth/auto-login HTTP/1.1
Host: <domínio-do-tenant-ou-localhost-com-tenant_schema>
Cookie: sessionid=<...>
Accept: application/json
```

**Query (opcional):**

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `tenant_schema` | Sim, se o utilizador tiver **mais do que um** tenant activo (`TenantMembership`). | `schema_name` do `Customer` (ex.: `acme_corp`). |

Se o utilizador tem um único membership, o tenant é inferido pelo **cabeçalho `Host`** (deve corresponder a um `Domain` registado). Sem `Host` válido: `400`.

### Resposta `200 OK`

| Campo | Tipo | Descrição |
|--------|------|-------------|
| `access_token` | string | JWT Langflow (utilizador de serviço do tenant). |
| `api_key` | string | API key Langflow para `x-api-key` / chamadas autenticadas. |
| `workspace_id` | string | UUID do project Langflow (`Customer.langflow_workspace_id`). |
| `langflow_user_id` | `null` | Deprecated; reservado para compatibilidade; sempre `null` neste fluxo. |

Exemplo:

```json
{
  "access_token": "<jwt>",
  "api_key": "<api-key>",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "langflow_user_id": null
}
```

### Erros

| Status | Quando ocorre |
|--------|----------------|
| `400` | `Host` em falta; ou utilizador com **vários** tenants sem `tenant_schema`. |
| `401` | Sem sessão válida (não autenticado no RID). |
| `403` | Sem `TenantMembership` activo para o tenant resolvido; ou sem membership em nenhum tenant. |
| `404` | `tenant_schema` desconhecido; ou domínio sem `Domain` registado. |
| `409` | `Customer.langflow_workspace_id` ainda `null` (workspace não provisionado). |
| `502` | Langflow indisponível ou resposta inválida (sem `access_token` / `api_key`). |

---

## Saúde da integração (placeholder)

Existe um router com prefixo `/langflow` e rota `GET /langflow/health` na aplicação FastAPI. O URL público exacto face ao mount `/api` pode variar; trate como **não contractu** até haver testes ou documentação de produto que o fixem.

---

## OpenAPI

Em modo de desenvolvimento (`DJANGO_DEBUG=true`), a especificação OpenAPI do RID pode estar disponível em `/api/openapi.json` e a UI em `/api/docs`, conforme `api/main.py`.

## Ver também

- [Guia de integração Langflow](../guides/langflow-bridge-integration.md)
- [ADR-009](../adr/ADR-009-langflow-database-integration.md)
